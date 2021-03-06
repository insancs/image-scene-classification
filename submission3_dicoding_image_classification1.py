# -*- coding: utf-8 -*-
"""Submission3_Dicoding_Image Classification1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vEgIbqEjY_lB4cvpvLmEIx5ICwjIqrnd

# Kaggle Configuration
"""

! pip install kaggle

! mkdir ~/.kaggle

! cp kaggle.json ~/.kaggle/

! chmod 600 ~/.kaggle/kaggle.json

"""# Download Dataset"""

! kaggle datasets download puneet6060/intel-image-classification

"""# Import Library"""

from random import randint
import zipfile
import os
import cv2        
import numpy as np
import matplotlib.pyplot as plt 
import seaborn as sn; sn.set(font_scale=1.4)
from sklearn.utils import shuffle    

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import Callback
from tensorflow.keras.callbacks import ReduceLROnPlateau
from tensorflow.keras.callbacks import EarlyStopping
print(tf.__version__)

"""# Extract Dataset"""

local_zip = 'intel-image-classification.zip'
zip_ref = zipfile.ZipFile(local_zip, 'r')
zip_ref.extractall('/tmp')
zip_ref.close()

print(os.listdir('/tmp/'))
print(os.listdir('/tmp/seg_train/seg_train'))
print(os.listdir('/tmp/seg_test/seg_test'))

train_dir = '/tmp/seg_train/seg_train'
validation_dir = '/tmp/seg_test/seg_test'

# Define Image Loader function
def get_images(directory):
    Images = []
    Labels = []  # 0 for Building , 1 for forest, 2 for glacier, 3 for mountain, 4 for Sea , 5 for Street
    label = 0
    
    for labels in os.listdir(directory): #Main Directory where each class label is present as folder name.
        if labels == 'glacier': #Folder contain Glacier Images get the '2' class label.
            label = 2
        elif labels == 'sea':
            label = 4
        elif labels == 'buildings':
            label = 0
        elif labels == 'forest':
            label = 1
        elif labels == 'street':
            label = 5
        elif labels == 'mountain':
            label = 3
        
        for image_file in os.listdir(directory + labels): #Extracting the file name of the image from Class Label folder
            image = cv2.imread(directory + labels + r'/' + image_file) #Reading the image (OpenCV)
            image = cv2.resize(image,(150,150)) #Resize the image, Some images are different sizes. (Resizing is very Important)
            Images.append(image)
            Labels.append(label)
    
    return shuffle(Images, Labels, random_state=817328462) #Shuffle the dataset you just prepared.

# Define class label function
def get_classlabel(class_code):
    labels = {2:'glacier', 4:'sea', 0:'buildings', 1:'forest', 5:'street', 3:'mountain'}
    
    return labels[class_code]

#Get the images and labels from the folders.
images, labels = get_images('/tmp/seg_train/seg_train/') 

#converting the list of images to numpy array.
images = np.array(images)
labels = np.array(labels)

"""# Image Sample"""

# Visualize image sample
f,ax = plt.subplots(5,5) 
f.subplots_adjust(0,0,3,3)
for i in range(0,5,1):
    for j in range(0,5,1):
        rnd_number = randint(0,len(images))
        ax[i,j].imshow(images[rnd_number])
        ax[i,j].set_title(get_classlabel(labels[rnd_number]))
        ax[i,j].axis('off')

"""# Image Data Generator"""

# Image augmentation
train_datagen = ImageDataGenerator(
    rescale = 1./255,
    rotation_range = 20,
    horizontal_flip = True,
    shear_range = 0.2,
    fill_mode = 'wrap',
    validation_split = 0.2
)

validation_datagen = ImageDataGenerator(rescale = 1./255,
                                        validation_split = 0.2)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size = (150, 150),
    class_mode = 'categorical',
    batch_size = 64,
    subset = 'training'
)

validation_generator = validation_datagen.flow_from_directory(
    train_dir,
    target_size = (150, 150),
    class_mode = 'categorical',
    batch_size = 64,
    subset = 'validation'
)

BATCH_SIZE = 64
STEPS_PER_EPOCH = 11230 / BATCH_SIZE

"""# Build the Model"""

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation = 'relu', input_shape = (150, 150, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(64, (3, 3), activation = 'relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.5), 
    tf.keras.layers.Dense(64, activation = 'relu'), 
    tf.keras.layers.Dense(6, activation = 'softmax')
])

model.summary()

# count loss function and optimizer
model.compile(
    loss = 'categorical_crossentropy',
    optimizer = tf.optimizers.Adam(),
    metrics = ['accuracy']               
)

"""## Create Callbacks"""

# Define callback
class myCallback(Callback):
    def on_train_begin(self, logs=None):
        print("Starting training")

    def on_train_end(self, logs=None):
        print("Training has been stopped")
        print('Accuracy = %2.2f%%' %(logs['accuracy'] * 100), '\nValidation Accuracy = %2.2f%%' %(logs['val_accuracy'] * 100))

    def on_epoch_begin(self, epoch, logs=None):
        print("Start epoch {} of training".format(epoch + 1))
    
    def on_epoch_end(self, epoch, logs={}):
      if(logs.get('accuracy') > 0.92) and (logs.get('val_accuracy') > 0.92):
        self.model.stop_training = True


reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2,
                              patience=5, min_lr=0.001)

early_stopping = EarlyStopping(monitor='loss', patience=3)

history = model.fit(train_generator,
                    steps_per_epoch = STEPS_PER_EPOCH,
                    epochs = 50,
                    batch_size = BATCH_SIZE,
                    validation_data = validation_generator,
                    callbacks = [myCallback(), reduce_lr, early_stopping]
                    )

"""# Plotting Accuracy and Loss"""

# Define accuracy
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

epochs = range(len(acc))

# Plotting accuracy
plt.figure(figsize=(8, 6))
plt.plot(epochs, acc, 'r', label='Training Accuracy')
plt.plot(epochs, val_acc, 'b', label='Validation Accuracy')
plt.title('Training and Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend(loc='lower right')
plt.show()

# Defina loss
loss = history.history['loss']
val_loss = history.history['val_loss']

# Plotting loss 
plt.figure(figsize=(8, 6))
plt.plot(epochs, loss, 'r', label='Training Loss')
plt.plot(epochs, val_loss, 'b', label='Validation Loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Lost')
plt.legend(loc='upper right')
plt.grid(False)
plt.show()

"""# Save the Model to TF-Lite"""

# Convert the model
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the model to tf-lite
with tf.io.gfile.GFile('model.tflite', 'wb') as f:
  f.write(tflite_model)