

import numpy as np
import cv2 as cv
from google.colab.patches import cv2_imshow
import matplotlib.pylab as plt
import math as math
from collections import defaultdict
from itertools import product
from numpy.linalg import inv



def center_mean(array, row, col, size): # Function used to calculate the average of the patches.

    # Use min & max to handle edges
    row_min = max(0, row - size)
    row_max = min(len(array), row + size)

    col_min = max(0, col-size)
    col_max = min(len(array[0]), col + size)

    # Get just the rows we want:
    sub_rows = array[row_min:row_max + 1]

    total = 0.0
    for row in sub_rows:
        # Now take just the cols we want:
        new_row = row[col_min:col_max + 1]
        total += sum(new_row)

    return total / (size*2 + 1)**2



def convolution(image,filter) : 
  n=filter.shape[0]
  n=int(np.floor(n/2))
  newimage=np.zeros(image.shape)
  #for x in range(0,image.shape[2]):
  for i in range(n,image.shape[0]-n):
    for j in range(n,image.shape[1]-n):
      newimage[i,j]=np.sum(image[i-n:i+n+1,j-n:j+n+1]*filter)

  newimage *= 255.0 / newimage.max()
  return newimage


def dnorm(x, mu, sd):
    return 1 / (np.sqrt(2 * np.pi) * sd) * np.e ** (-np.power((x - mu) / sd, 2) / 2)

def gaussian_kernel(size, sigma=1):
 
    kernel_1D = np.linspace(-(size // 2), size // 2, size)
    for i in range(size):
        kernel_1D[i] = dnorm(kernel_1D[i], 0, sigma)
    kernel_2D = np.outer(kernel_1D.T, kernel_1D.T)
 
    kernel_2D *= 1.0 / kernel_2D.max()
    return kernel_2D




def SobelX(img):
  filter = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
  cx=convolution(img,filter)
  return cx
def SobelY(img):
  filter = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
  cy=convolution(img, np.flip(filter.T, axis=0))
  return cy

def cornerDetection(grey,threshold): # Calculate the determinant of the Harris trace.
  x_Der=SobelX(grey)
  y_Der=SobelY(grey)

  xy_Der = np.multiply(x_Der,y_Der)

  x_Der = np.square(x_Der)
  y_Der = np.square(y_Der)

  x_Der = convolution(x_Der,kernel)
  y_Der = convolution(y_Der,kernel)
  xy_Der = convolution(xy_Der,kernel)

  R=np.multiply(x_Der,y_Der)
  R=np.subtract(R,xy_Der)

  sum_Der=np.add(x_Der,y_Der)
  sum_Der=np.square(sum_Der)

  R=np.subtract(R,0.05*sum_Der)

  R *= 255.0 / R.max()



  corners=[]

  for x in range(R.shape[0]):
    for y in range(R.shape[1]):
      if (R[x,y]>threshold):
        corners.append([x,y])
  return corners,R


def matching_Sets(image,image1,corners, corners1,patch_Size): # Function used for pairing. (ZMSSD)
  scores=defaultdict(int)
  patch_Size=int(patch_Size/2)
  for x,y in corners:
    
    for a,b in corners1:
      s=0
      mu=center_mean(image,x,y,patch_Size)
      mu1=center_mean(image1,a,b,patch_Size)
      for p,q in product(range(-patch_Size,patch_Size+1),range(-patch_Size,patch_Size+1)):
        if (x+p>0 and x+p<image.shape[0] and y+q>0 and y+q<image.shape[1] and a+p>0 and a+p<image1.shape[0] and b+q>0 and b+q<image1.shape[1]):

          s+=(image[x+p,y+q]-mu+mu1-image1[a+p,b+q])**2
      scores[x,y,a,b]=s
  return scores

kernel_size=5
kernel=gaussian_kernel(kernel_size, sigma=math.sqrt(kernel_size))

img=cv.imread('/content/drive/MyDrive/TP1_IMAGE_PROCESS/set1-1.png')
grey = cv.cvtColor(img, cv.COLOR_BGR2GRAY )

corners,R=cornerDetection(grey,80)


img1=cv.imread('/content/drive/MyDrive/TP1_IMAGE_PROCESS/set1-2.png')

grey1 = cv.cvtColor(img1, cv.COLOR_BGR2GRAY )
corners1,R1=cornerDetection(grey1,110)

for a,b in corners: # Tracer les coins trouvés
  plt.scatter(b, a, s=25, c='red', marker='o')
for c,d in corners1:
  plt.scatter(d+517, c, s=25, c='red', marker='o')

plot_image = np.concatenate((img, img1), axis=1)
plt.imshow(plot_image)
plt.show()

scores=matching_Sets(grey,grey1,corners,corners1,11)

sorted_Scores=sorted(scores.items(),key=lambda item: item[1]) # Sorting the pairing array.
matches=[]

th=3

for x,y in sorted_Scores:
  a,b,c,d=x
  if (all((abs(a-x)>1 or abs(b-y)>1) and (abs(c-z)>th or abs(d-q)>th) for x,y,z,q in matches)): # Avoid taking pairings that are too close to eachother, as in to avoid duplications.
      matches.append((a,b,c,d))

for a,b,c,d in matches: # Visualization of the pairings.
  plt.scatter(b, a, s=25, c='red', marker='o')
for a,b,c,d in matches:
  plt.scatter(d+517, c, s=25, c='red', marker='o')

for a,b,c,d in matches:
  point1 = [b, a]
  point2 = [d+517, c]

  x_values = [point1[0], point2[0]]

  y_values = [point1[1], point2[1]]
  plt.plot(x_values, y_values,'b', linestyle="--",linewidth=0.75)


plot_image = np.concatenate((img, img1), axis=1)
plt.imshow(plot_image)
plt.show()

from numpy.linalg import inv
import random
from collections import defaultdict


def vote(H,x1,y1,x2,y2,t): # Voting function (RANSAC)

  x = np.array([x1,y1,1])
  xprime = np.array([x2,y2,1])
  x= x.reshape([3,1])
  xprime=xprime.reshape([3,1])

  Hx = np.matmul(H,x)
  Hx = Hx / Hx[2]
  result = np.subtract(Hx,xprime)
  if (np.linalg.norm(result) < t):
    return 1
  else : return 0


votes=defaultdict(int)

inliers={}




for T in range (0,500): # 500 Iterations to find the H Matrix.
  matrix = []
  p=[]
  
  for i in range (0,4):
    ps=random.randrange(0,len(matches)-1)
    while (all(ps!=px for px in p)==False):
      ps=random.randrange(0,len(matches)-1)
    p.append(ps)
  A=[]
  x=[]
  for k in p:
    for a,b,c,d in matches[k:k+1]:
      nt=[a,b,1,0,0,0,-a*c,-b*c]
      A.append(nt)
      nt=[0,0,0,a,b,1,-a*d,-b*d]
      A.append(nt)
      x.append(c)
      x.append(d)

  if (np.linalg.det(A) == 0 ) : continue
  A=np.array(A)
  Ainv = np.linalg.inv(A)
  x=np.array(x)
  x=x.reshape([8,1])
  H=np.matmul(Ainv,x)
  H=list(H)
  H.append(1)
  H=np.array(H)
  H=H.reshape(3,3)

  for a,b,c,d in matches:
    votes[p[0],p[1],p[2],p[3]]+= vote(H,a,b,c,d,5)

    if (vote(H,a,b,c,d,5)):
      matrix.append([a,b,c,d])
  inliers[p[0],p[1],p[2],p[3]] = matrix

#Recherche de la meilleure matrice H

A=[]
x=[]
for a,b,c,d in inliers[59, 72, 45, 8]:  # Here put the best inlier found.
    nt=[a,b,1,0,0,0,-a*c,-b*c]
    A.append(nt)
    nt=[0,0,0,a,b,1,-a*d,-b*d]
    A.append(nt)
    x.append(c)
    x.append(d)
A=np.array(A)

A.shape
x=np.array(x)
x=x.reshape([20,1])
u,d,v=np.linalg.svd(A)

uT = np.matrix.transpose(u)

xpri = np.matmul(uT,x)


xpri = xpri[0:8]

d = np.reshape(d,[8,1])

xpri=np.divide(xpri,d)
xpri

Ho = np.matmul(v,xpri)

Ho=np.append(Ho,[1])

Ho=Ho.reshape([3,3]) # This is the best Homography matrix H found.

# Tracé des appariements des inliers
for a,b,c,d in inliers[21, 19, 13, 7]:
  plt.scatter(b, a, s=25, c='red', marker='o')
for a,b,c,d in inliers[21, 19, 13, 7]:
  plt.scatter(d+517, c, s=25, c='red', marker='o')

for a,b,c,d in inliers[21, 19, 13, 7]:
  point1 = [b, a]
  point2 = [d+517, c]

  x_values = [point1[0], point2[0]]

  y_values = [point1[1], point2[1]]
  plt.plot(x_values, y_values,'b', linestyle="--",linewidth=0.75)

plot_image = np.concatenate((img, img1), axis=1)
plt.imshow(plot_image)
plt.show()

len(matches)
