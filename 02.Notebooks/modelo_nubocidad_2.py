import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.utils import Sequence
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, precision_recall_fscore_support, accuracy_score

# Verificar GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print("GPU detectada:")
    for gpu in gpus:
        print(gpu)
else:
    print("No se detectó GPU. Se usará CPU.")

# Ruta del dataset
base_dir = r'C:\Users\Florencia\Desktop\ProyectoNubes\04.Imagenes_validacion_manual - copia'

# Cargar imágenes y etiquetas
image_paths = []
octa_labels = []

for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    try:
        octa = int(folder.split('_')[-1])
    except ValueError:
        continue
    for fname in os.listdir(folder_path):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_paths.append(os.path.join(folder_path, fname))
            octa_labels.append(octa)

# Visualización del balanceo de clases
plt.figure(figsize=(8, 4))
sns.countplot(x=octa_labels)
plt.title("Distribución de clases (Octas)")
plt.xlabel("Nivel de Octa")
plt.ylabel("Cantidad de imágenes")
plt.savefig("distribucion_clases_octas.png")
plt.show()

# División 80/20
train_paths, val_paths, train_labels, val_labels = train_test_split(
    image_paths, octa_labels, test_size=0.2, random_state=42, stratify=octa_labels
)

# Codificación one-hot
train_labels_cat = tf.keras.utils.to_categorical(train_labels, num_classes=9)
val_labels_cat = tf.keras.utils.to_categorical(val_labels, num_classes=9)

# Calcular pesos de clase
class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(octa_labels), y=octa_labels)
class_weights_dict = dict(enumerate(class_weights))

# Generador personalizado
class OctaDataGenerator(Sequence):
    def __init__(self, image_paths, labels, batch_size, img_width, img_height, augment=False, **kwargs):
        super().__init__(**kwargs)
        self.image_paths = image_paths
        self.labels = labels
        self.batch_size = batch_size
        self.img_width = img_width
        self.img_height = img_height
        self.augment = augment
        self.indexes = np.arange(len(self.image_paths))
        self.on_epoch_end()
        self.augmenter = tf.keras.preprocessing.image.ImageDataGenerator(
            rescale=1./255,
            rotation_range=10 if self.augment else 0,
            width_shift_range=0.1 if self.augment else 0.0,
            height_shift_range=0.1 if self.augment else 0.0,
            brightness_range=[0.8, 1.2] if self.augment else None,
            horizontal_flip=self.augment
        )

    def __len__(self):
        return int(np.ceil(len(self.image_paths) / self.batch_size))

    def __getitem__(self, index):
        batch_paths = self.image_paths[index * self.batch_size:(index + 1) * self.batch_size]
        batch_labels = self.labels[index * self.batch_size:(index + 1) * self.batch_size]
        batch_images = []

        for path in batch_paths:
            try:
                img = load_img(path, target_size=(self.img_height, self.img_width))
                img = img_to_array(img)
                batch_images.append(img)
            except Exception as e:
                print(f"Error al cargar imagen: {path} — {e}")
                continue

        if len(batch_images) == 0:
            return np.zeros((0, self.img_height, self.img_width, 3)), np.zeros((0, 9))

        batch_images = np.array(batch_images).astype('float32')
        batch_images = next(self.augmenter.flow(batch_images, batch_size=len(batch_images), shuffle=False))
        batch_labels = tf.keras.utils.to_categorical(batch_labels[:len(batch_images)], num_classes=9)
        return batch_images, batch_labels
        

    def on_epoch_end(self):
        temp = list(zip(self.image_paths, self.labels))
        np.random.shuffle(temp)
        self.image_paths, self.labels = zip(*temp)

# Parámetros
img_width = 224
img_height = 224
batch_size = 32

train_generator = OctaDataGenerator(train_paths, train_labels, batch_size, img_width, img_height, augment=True)
val_generator = OctaDataGenerator(val_paths, val_labels, batch_size, img_width, img_height, augment=False)

# Modelo CNN
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(img_height, img_width, 3)),
    MaxPooling2D(2, 2),
    Dropout(0.3),

    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Dropout(0.3),

    GlobalAveragePooling2D(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(9, activation='softmax')
])

model.compile(optimizer=Adam(learning_rate=0.001),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Callbacks
#early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True, verbose=1)
checkpoint_path = 'mejor_modelo_octa.h5'
model_checkpoint = ModelCheckpoint(checkpoint_path, monitor='val_loss', save_best_only=True, verbose=1)

# Entrenamiento
history = model.fit( train_generator, validation_data=val_generator, epochs=400, class_weight=class_weights_dict, callbacks=[model_checkpoint]
)

# Predicciones
preds = model.predict(val_generator)
y_pred_octa = np.argmax(preds, axis=1)
octa_true = [int(os.path.basename(os.path.dirname(path)).split('_')[-1]) for path in val_paths]

# Matriz de confusión
cm = confusion_matrix(octa_true, y_pred_octa)
plt.figure(figsize=(8, 6))
ConfusionMatrixDisplay(cm, display_labels=[str(i) for i in range(9)]).plot(cmap='Blues')
plt.title("Matriz de Confusión - Clasificación de Octas")
plt.savefig("matriz_confusion_octas.png")
plt.show()

# Métricas por clase
precision, recall, f1, _ = precision_recall_fscore_support(octa_true, y_pred_octa, labels=list(range(9)), zero_division=0)
accuracy = accuracy_score(octa_true, y_pred_octa)

df_metrics = pd.DataFrame({
    "Clase": list(range(9)),
    "Precision": precision,
    "Recall": recall,
    "F1-score": f1
})
df_metrics.loc[len(df_metrics.index)] = ["Accuracy Global", accuracy, "", ""]
df_metrics.to_csv("metricas_modelo_octas.csv", index=False)

# Visualización de errores
errores = [(path, true, pred) for path, true, pred in zip(val_paths, octa_true, y_pred_octa) if true != pred]
plt.figure(figsize=(12, 12))
for i, (path, true, pred) in enumerate(errores[:9]):
    img = load_img(path, target_size=(img_height, img_width))
    plt.subplot(3, 3, i + 1)
    plt.imshow(img)
    plt.title(f"Real: {true} - Pred: {pred}")
    plt.axis('off')
plt.tight_layout()
plt.savefig("errores_clasificacion_octas.png")
plt.show()

# Guardar errores en CSV con trazabilidad
df_errores = pd.DataFrame(errores, columns=["Ruta", "Etiqueta Real", "Predicción"])
df_errores["Carpeta"] = df_errores["Ruta"].apply(lambda x: os.path.basename(os.path.dirname(x)))
df_errores.to_csv("errores_clasificacion.csv", index=False)
print("Archivo 'errores_clasificacion.csv' guardado con éxito.")

# Gráfico de aprendizaje
hist = history.history
epochs = range(1, len(hist['loss']) + 1)

plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(epochs, hist['loss'], label='Train Loss')
plt.plot(epochs, hist['val_loss'], label='Validation Loss')
plt.title('Loss por época')
plt.xlabel('Épocas')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(epochs, hist['accuracy'], label='Train Accuracy')
plt.plot(epochs, hist['val_accuracy'], label='Validation Accuracy')
plt.title('Accuracy por época')
plt.xlabel('Épocas')
plt.ylabel('Accuracy')
plt.legend()

plt.tight_layout()
plt.savefig("grafico_aprendizaje_octas.png")
plt.show()