import matplotlib.pyplot as plt
import numpy as np

from .draw_utils import COLOR, LINE_STYLE


def draw_success_precision(success_ret, name, attrs, precision_ret=None,
       norm_precision_ret=None, bold_name=None, axis=[0, 1]):
   # success plot
   fig, ax = plt.subplots()
   fig.set_size_inches(8, 6)
   ax.grid(b=True)
#    ax.set_aspect(1)
   plt.xlabel('Overlap threshold')
   plt.ylabel('Success rate')
   plt.title(r'\textbf{Success plots of OPE on %s}' % (name))
   plt.axis([0, 1]+axis)
   success = {}
   thresholds = np.arange(0, 1.05, 0.05)
   for idx, (attr, videos) in enumerate(attrs):
       value = [v for k, v in success_ret['SiamFC'].items() if k in videos]
       success[attr] = np.mean(value)

       if attr == bold_name:
           label = r"\textbf{[%.3f] %s}" % (success[attr], attr)
       else:
           label = "[%.3f] " % success[attr] + attr
       plt.plot(thresholds, np.mean(value, axis=0),
               color=COLOR[idx], linestyle=LINE_STYLE[idx],label=label, linewidth=2)
   ax.legend(loc='lower left', labelspacing=0.2)
   ax.autoscale(enable=True, axis='both', tight=True)
   xmin, xmax, ymin, ymax = plt.axis()
   ax.autoscale(enable=False)
   ymax += 0.03
   ymin = 0
   plt.axis([xmin, xmax, ymin, ymax])
   plt.xticks(np.arange(xmin, xmax+0.01, 0.1))
   plt.yticks(np.arange(ymin, ymax, 0.1))
   ax.set_aspect((xmax - xmin)/(ymax-ymin))
   plt.savefig('success plot.png', dpi = 300)
   plt.show()

   if precision_ret:
       # norm precision plot
       fig, ax = plt.subplots()
       ax.grid(b=True)
       fig.set_size_inches(8, 6)
       ax.set_aspect(50)
       plt.xlabel('Location error threshold')
       plt.ylabel('Precision')
       plt.title(r'\textbf{Precision plots of OPE - %s}' % (name))
       plt.axis([0, 50]+axis)
       precision = {}
       thresholds = np.arange(0, 51, 1)
       for idx, (attr, videos) in enumerate(attrs):
           value = [v for k, v in precision_ret['SiamFC'].items() if k in videos]
           precision[attr] = np.mean(value, axis=0)[20]

           if attr == bold_name:
               label = r"\textbf{[%.3f] %s}" % (precision[attr], attr)
           else:
               label = "[%.3f] " % (precision[attr]) + attr
           plt.plot(thresholds, np.mean(value, axis=0),
                   color=COLOR[idx], linestyle=LINE_STYLE[idx],label=label, linewidth=2)
       ax.legend(loc='lower right', labelspacing=0.2)
       ax.autoscale(enable=True, axis='both', tight=True)
       xmin, xmax, ymin, ymax = plt.axis()
       ax.autoscale(enable=False)
       ymax += 0.03
       ymin = 0
       plt.axis([xmin, xmax, ymin, ymax])
       plt.xticks(np.arange(xmin, xmax+0.01, 5))
       plt.yticks(np.arange(ymin, ymax, 0.1))
       ax.set_aspect((xmax - xmin)/(ymax-ymin))
       plt.savefig('precision plot.png', dpi = 300)
       plt.show()