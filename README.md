This code is a debugged version of the code provided by "Zhenghao Zhao" at this link.: https://github.com/zzh142857/SiameseFC-tf
# SiamFC-tf
This repository is the tensorflow implementation of both training and evaluation of SiamFC described in the paper [*Fully-Convolutional Siamese nets for object tracking*](https://www.robots.ox.ac.uk/~luca/siamese-fc.html).   
The code is revised on the base of the evaluation-only version code from the repository of the auther of this paper(https://github.com/torrvision/siamfc-tf).


## Training Step
Step by step explanation of the whole model and training process.
### 2.1 Prepare training data
One training sample consists of an examplar image: **z**, a search image : **x**, and their correspnding ground truth information: **z_pos_x, z_pos_y, z_target_w, z_target_h and x_pos_x, x_pos_y, x_target_w, x_target_h**. Note the coordinates of the target have been converted to the center of bbox from the lefttop corner through function *src.region_to_bbox.py*. <br>
<br>
We pick the neibored two images in a vedio as z and x, and get a shuffled training data set from all 180 vedios in validation data from GOT-10K data set. And for conveniece of later steps, we resize all images to a uniform size [*design.resize_width, design.resize_height*]. The training data set is saved in a tfrecord file.

### 2.2 Pad & Crop the image
Before entering the conv network, we crop **z** and **x** to certain sizes, and pad with the mean RGB value of each image if the crop region exceeds the orignal image size.<br>
<br>
According to the paper, the croped **z** should contains the area of the marginal bbox on the original image, where the margin *2p = (w + h) / 2*, and this marginal context will then be resized to a constant size: [*design.exemplar_sz, design.exemplar_sz*], which is [127, 127] in our training process. <br>
<br>
Cropping step of **x** is the same, but only all the sizes are larger by a facter: *desing.search_sz / desing_examplar_sz* and the center of cropping is the center of target position in **x** instead of **z**. In addition, cause the evaluation process needs to inference three different scales of **x** to implement the update on target scale, here in training process, we also crop three **x** samples, but with the same size. (The last sample actually has a little bit larger size due to the way we crop the image, but this doesn't matter.)

### 2.3 Siamese conv net
When entering the conv net, **x** tensor has a shape of [*batch_size × 3, desing.search_sz, desing.search_sz, channel*], and **z** tensor has a shape of [*batch_size, design.exemplar_sz, design.exemplar_sz, channel*]. <br>
<br>
**x** and **z** will go to the same conv net, for which we adopt a Alexnet architecture. The parameters of the net are defined in *design.filter_w, ...* and *src.siamese._conv_stride, ...*.<br>
<br>
To match the shape of triple scaled **x** feature map, we then stack the **z** feature map for three times.

### 2.4 Cross Correlation
We calcualte a score map by implementing a cross correlation between the extracted feature map of **z** and **x**.<br><br>
First the feature map of **z** is transposed and reshaped to [*w, h, batch_size × feature_channel × 3, 1*], and the feature map of **x** is reshaped to [*1, w, h, batch_size × feature_channel × 3*]. <br>
<br>
Then we calculate the depthwise_conv2d of **x** feature with respect to **z** feature as the filter. Output tensor of this step has a shape of [*1, w, h, batch_size × feature_channel × 3*].<br>
<br>
This output tensor will further be splited and concatebated to a final shape of [*batch_size × 3, w, h, feature_channel*]. Then the final score map is generated by reduce_sum through all the feature_channels.

### 2.5 Metrics
The score map is resized to the same size of the cropped **x** image by bilinear interpolation, from which we pick the top-3 scores and calculate their average coordinate as the predicted target position. Metrics such as distance to ground truth can then be calculated.<br>
<br>
The logistic loss of the predicted score map is defined as: $\frac{1}{D}\sum_{u \in D}\log{(1 + e^{-y(u)v(u)})}$, where *D* represent all the pixels on the score map. And the value of the ground thruth label *v(u)* is *+1* if it is within the ground thruth bbox, and *-1* if not.<br>
<br>
We adopt the adamoptimizer with an initial learning rate of *1e-6* to minimize the loss.

## 3 Tracking Algorithm
Given the first frame and its bbox, predict the bbox for the following frames. 
### 3.1 Inference
Input the first frame into model as **z**, and input the second frame as **x**, *batch_size* is one in tracking process.<br>
<br>
Here we crop three different scale smaples for **x** with the factor of $1.04^{-2}, 1, 1.04^{2}$. 
### 3.2 Finalize the score map
The output of the inference model is a [*1, design.search_sz, design.search_sz, 3*] score map, in which *1* correspond to unit *batch_size* and *3* correspond to the three different scaled **x** samples.
#### 3.2.1 Penalize change of scale
We first squeeze the unit dimension in score map, and split into three [*design.search_sz, design.search_sz*] score maps represent the prediction at three scales. We then apply a penalty for the change of scale, the first and third score map are multiplied with factor *hp.scale_penalty*, which is *0.97* from the original paper.
#### 3.2.2 Update scale
Select the scale from three score maps who has the largest maximum score, and update the target scale with a learning rate of *hp.scale_lr = 0.59*: $x\_sz = (1-hp.scale\_lr) * x\_sz + hp.scale\_lr * scale\_factor$, where the scale factor can be $1.04^{-2}, 1, 1.04^{2}$. <br>
<br>
This will update the cropping area of **x**, but the size of the final cropped image still remains the same, just the image will be stretched more.
#### 3.2.3 Normalize score map
The selected score is then  substracted by the smallest score on the map, and divided by the sum of all scores.
#### 3.2.4 Penalize displacement
A cosine shape window is added to the normalized score map to penalize the displacement of the target: $score map = (1-hp.window\_influence)*score map + hp.window\_influence*penalty$.
### 3.3 Get predicted position
Get the index of the highest score on the map, and recover the displacement on the original **x** image by dividing the resize facter when we crop the image: $displacement *= x\_sz / design.search\_sz$. And we can get the width and height of the target bbox with the updated scale.
### 3.4 Next iteration
**x** of the current prediction will be used as **z** for the prediction of next frame. So we use the predicted position and scale(???) to crop the original **x** image as the new **z**. This new cropped **z** is then send to conv net and generate a new **z** feature map. We then update it with a rolling average: $z\_feature\_map = (1-hp.z\_lr)*old\_z\_feature\_map + hp.z\_lr*new\_z\_feature\_map$.

# User Guide for the code
## Preparation
1) Clone the repository
`git clone https://github.com/zzh142857/SiameseFC-tf.git`   
2) The code is prepared for a environment with Python==3.6 and Tensorflow-gpu==1.6 with the required CUDA and CudNN library.   
3) Other packages can be installed by:   
`sudo pip install -r requirements.txt`   
4) Download training data cd to the directory where this README.md file located, then: mkdir data`   
Download [video sequences](http://got-10k.aitestunion.com/downloads_dataset/val_data) in `data` and unzip the archive.
The original model on the paper is trained with the ImageNet(ILSVRC15) dataset, which has millions of labeled images. For simplicity, we only use GOT-10K Validation data set for training and OTB100 for validation. The training data contains 180 vedios, which total around 20000 thousand images.
5) Prepare tfrecord file for training data   
To reduce the time for reading images during training, we write all the training data into a single tfrecord file.   
Execute `python3 get_shuffled_list_from_vedio.py` to generate a shuffled list of information of all examplar search imge pairs for training.   
Then`python3 prepare_training_dataset.py` to write the real data into a tfrecord file.
## Training model
1) Set parameters:
Parameters for training process are defined in `parameters.design.json`, `parameters.environment.json` and `parameters.hyperparams.json`. 
Make sure the path for tfrecord, checkpoint saver are correct, and one can also customize the model parameters at will.   
2) Execute training scripts 
`python run_tracker_training.py`   

## Running the tracker
1) Set `video` from `parameters.evaluation` to `"all"` or to a specific sequence (e.g. `"vot2016_ball1"`)
2) See if you are happy with the default parameters in `parameters/hyperparameters.json`
3) Optionally enable visualization in `parameters/run.json`
4) Call the main script (within an active virtualenv session)
`python run_tracker_evaluation.py`


## References
If you find our work useful, please consider citing the original authors

↓ [Original method] ↓
```
@inproceedings{bertinetto2016fully,
  title={Fully-Convolutional Siamese Networks for Object Tracking},
  author={Bertinetto, Luca and Valmadre, Jack and Henriques, Jo{\~a}o F and Vedaldi, Andrea and Torr, Philip H S},
  booktitle={ECCV 2016 Workshops},
  pages={850--865},
  year={2016}
}
```
↓ [Improved method and evaluation] ↓
```
@article{valmadre2017end,
  title={End-to-end representation learning for Correlation Filter based tracking},
  author={Valmadre, Jack and Bertinetto, Luca and Henriques, Jo{\~a}o F and Vedaldi, Andrea and Torr, Philip HS},
  journal={arXiv preprint arXiv:1704.06036},
  year={2017}
}
```

## License
This code can be freely used for personal, academic, or educational purposes.
Please contact us for commercial use.

