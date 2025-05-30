import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from model import ImageClassifier
from sklearn.exceptions import NotFittedError

class PetClassifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini projet")
        self.root.geometry("1000x800")
        
        # Initialize variables
        self.cat_images = []
        self.dog_images = []
        self.cat_labels = []
        self.dog_labels = []
        self.cat_db_path = "c:/Users/Lenovo/OneDrive/Desktop/Mini-Project/DB/CAT"
        self.dog_db_path = "c:/Users/Lenovo/OneDrive/Desktop/Mini-Project/DB/DOG"
        self.classifier = ImageClassifier()
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        self.train_tab = ttk.Frame(self.tab_control)
        self.test_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.train_tab, text='Entraînement')
        self.tab_control.pack(expand=1, fill="both")
        
        self.setup_training_tab()
        self.setup_testing_tab()

    def create_scrollable_frame(self, parent, width, height):
        canvas = tk.Canvas(parent, width=width, height=height)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_mousewheel(event, canvas):
            canvas.yview_scroll(int(-1 * (event.delta/60)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", lambda e: _on_mousewheel(e, canvas))
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
        return canvas, scrollbar, scrollable_frame

    def create_image_grid(self, parent, rows=2, cols=5, width=120, height=120):
        grid = tk.Frame(parent)
        grid.pack(pady=5)
        labels = []
        
        for i in range(rows):
            for j in range(cols):
                frame = tk.Frame(grid, width=width, height=height, relief='solid', bd=1)
                frame.grid(row=i, column=j, padx=2, pady=2)
                frame.grid_propagate(False)
                label = tk.Label(frame)
                label.place(relx=0.5, rely=0.5, anchor='center')
                labels.append(label)
        
        return labels

    def setup_training_tab(self):
        main_container = tk.Frame(self.train_tab)
        main_container.pack(fill='both', expand=True)
        
        # Left frame
        left_frame = tk.Frame(main_container, relief='solid', bd=1)
        left_frame.pack(side='left', fill='y', padx=5, pady=5)
        
        # Dataset title
        tk.Label(left_frame, text="Jeu de Données", font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Columns container
        columns_container = tk.Frame(left_frame)
        columns_container.pack(fill='both', expand=True, padx=5)
        
        # Create columns
        cat_column = tk.Frame(columns_container)
        dog_column = tk.Frame(columns_container)
        cat_column.pack(side='left', fill='both', expand=True, padx=2)
        dog_column.pack(side='left', fill='both', expand=True, padx=2)
        
        # Category labels
        tk.Label(cat_column, text="Chats", font=('Arial', 10)).pack(pady=2)
        tk.Label(dog_column, text="Chiens", font=('Arial', 10)).pack(pady=2)
        
        # Scrollable frames
        cat_canvas, cat_scrollbar, cat_scrollable = self.create_scrollable_frame(cat_column, 130, 400)
        dog_canvas, dog_scrollbar, dog_scrollable = self.create_scrollable_frame(dog_column, 130, 400)
        
        cat_canvas.pack(side="left", fill="both", expand=True)
        cat_scrollbar.pack(side="right", fill="y")
        dog_canvas.pack(side="left", fill="both", expand=True)
        dog_scrollbar.pack(side="right", fill="y")
        
        # Load dataset
        self.load_dataset_images(cat_scrollable, dog_scrollable)
        
        # Right frame
        right_frame = tk.Frame(main_container)
        right_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # Content frame
        content_frame = tk.Frame(right_frame)
        content_frame.pack(side='left', fill='both', expand=True)
        
        # Cat section with its button
        tk.Label(content_frame, text="Sélectionner 10 images de chats",
                font=('Arial', 10)).pack(pady=5)
        self.cat_labels = self.create_image_grid(content_frame)
        tk.Button(content_frame, text="Ajouter une image de chat",
                 command=lambda: self.add_image("cat")).pack(pady=2)
        
        # Dog section with its button
        tk.Label(content_frame, text="Sélectionner 10 images de chiens",
                font=('Arial', 10)).pack(pady=5)
        self.dog_labels = self.create_image_grid(content_frame)
        tk.Button(content_frame, text="Ajouter une image de chien",
                 command=lambda: self.add_image("dog")).pack(pady=2)
        
        # Train button
        train_container = tk.Frame(right_frame)
        train_container.pack(side='right', padx=5, fill='y')
        tk.Frame(train_container).pack(expand=True)
        
        train_button = tk.Button(
            train_container,
            text="Entraîner",
            command=self.train_model,
            width=10
        )
        train_button.pack(side='bottom', pady=10)

    def setup_testing_tab(self):
        main_container = tk.Frame(self.test_tab)
        main_container.pack(fill='both', expand=True)
        
        # Left sidebar
        left_frame = tk.Frame(main_container, relief='solid', bd=1)
        left_frame.pack(side='left', fill='y', padx=5, pady=5)
        
        tk.Label(left_frame, text="Nouvelle photo", font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.left_image_frame = tk.Frame(left_frame, relief='solid', bd=1, width=200, height=200)
        self.left_image_frame.pack(pady=5)
        self.left_image_frame.pack_propagate(False)
        
        self.left_image_label = tk.Label(self.left_image_frame)
        self.left_image_label.pack(expand=True)
        
        tk.Label(left_frame, text="Chat ou chien ou autre").pack(pady=2)
        
        tk.Button(left_frame, text="Parcourir",
                 command=self.select_test_image).pack(pady=5)
        
        # Right frame
        right_frame = tk.Frame(main_container)
        right_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        tk.Label(right_frame, text="Photo sélectionnée",
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.selected_image_frame = tk.Frame(right_frame, relief='solid', bd=1, width=300, height=300)
        self.selected_image_frame.pack(pady=5)
        self.selected_image_frame.pack_propagate(False)
        
        self.selected_image_label = tk.Label(self.selected_image_frame)
        self.selected_image_label.pack(expand=True)
        
        tk.Button(right_frame, text="Prédiction",
                 command=self.make_prediction).pack(pady=5)
        
        self.result_frame = tk.Frame(right_frame, relief='solid', bd=1)
        self.result_label = tk.Label(self.result_frame, text="",
                                   font=('Arial', 10, 'bold'))
        self.result_label.pack(pady=5)

    def train_model(self):
        if len(self.cat_images) < 10 or len(self.dog_images) < 10:
            if tk.messagebox.askokcancel("Avertissement",
                "Vous devez saisir des images\nVoulez-vous continuer sans entraînement ?",
                icon='warning'):
                self.tab_control.add(self.test_tab, text='Test')
                self.tab_control.select(self.test_tab)
            return
        
        self.classifier.train(self.cat_images, self.dog_images)
        self.tab_control.add(self.test_tab, text='Test')
        self.tab_control.select(self.test_tab)

    def add_image(self, category):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            img = Image.open(file_path)
            img = img.resize((120, 120))
            photo = ImageTk.PhotoImage(img)
            
            if category == "cat" and len(self.cat_images) < 10:
                self.cat_images.append(file_path)
                self.cat_labels[len(self.cat_images)-1].configure(image=photo)
                self.cat_labels[len(self.cat_images)-1].image = photo
            elif category == "dog" and len(self.dog_images) < 10:
                self.dog_images.append(file_path)
                self.dog_labels[len(self.dog_images)-1].configure(image=photo)
                self.dog_labels[len(self.dog_images)-1].image = photo

    def select_test_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Fichiers d'images", "*.jpg *.jpeg *.png")])
        if file_path:
            self.test_image_path = file_path
            img = Image.open(file_path)
            
            left_img = img.resize((180, 180))
            left_photo = ImageTk.PhotoImage(left_img)
            self.left_image_label.configure(image=left_photo)
            self.left_image_label.image = left_photo
            
            right_img = img.resize((280, 280))
            right_photo = ImageTk.PhotoImage(right_img)
            self.selected_image_label.configure(image=right_photo)
            self.selected_image_label.image = right_photo

    def make_prediction(self):
        if not hasattr(self, 'test_image_path'):
            tk.messagebox.showwarning("Avertissement", "Veuillez sélectionner une image d'abord !")
            return
            
        try:
            prediction, confidence = self.classifier.predict(self.test_image_path)
            self.update_prediction_result(prediction, confidence)
        except NotFittedError:
            tk.messagebox.showwarning("Avertissement",
                "Veuillez entraîner le modèle avant de faire des prédictions !")
            self.tab_control.select(self.train_tab)

    def load_dataset_images(self, cat_container, dog_container):
        self.dataset_cat_images = []
        self.dataset_dog_images = []
        
        for img_name in os.listdir(self.cat_db_path):
            img_path = os.path.join(self.cat_db_path, img_name)
            self.dataset_cat_images.append(img_path)
            self.add_dataset_image(cat_container, img_path)
        
        for img_name in os.listdir(self.dog_db_path):
            img_path = os.path.join(self.dog_db_path, img_name)
            self.dataset_dog_images.append(img_path)
            self.add_dataset_image(dog_container, img_path)
            
        if self.dataset_cat_images and self.dataset_dog_images:
            self.classifier.train(self.dataset_cat_images, self.dataset_dog_images)

    def update_prediction_result(self, prediction, confidence):
        self.result_frame.pack_forget()
        self.result_frame.pack(pady=5, fill='x', padx=5)
        self.result_label.configure(text=f"{prediction} ({int(confidence)}%)")

    def add_dataset_image(self, container, img_path):
        try:
            img = Image.open(img_path)
            img = img.resize((120, 120))
            photo = ImageTk.PhotoImage(img)
            
            frame = tk.Frame(container, relief='solid', bd=1)
            frame.pack(fill='x', padx=2, pady=2)
            
            label = tk.Label(frame, image=photo, cursor='hand2')
            label.image = photo
            
            category = 'cat' if 'CAT' in img_path else 'dog'
            label.bind('<Button-1>',
                lambda e, path=img_path, cat=category: self.select_from_dataset(path, cat))
            label.pack()
            
            return label
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            return None

    def select_from_dataset(self, img_path, category):
        if category == "cat" and len(self.cat_images) >= 10:
            return
        if category == "dog" and len(self.dog_images) >= 10:
            return

        try:
            img = Image.open(img_path)
            img = img.resize((120, 120))
            photo = ImageTk.PhotoImage(img)
            
            if category == "cat":
                idx = len(self.cat_images)
                if idx < len(self.cat_labels):
                    self.cat_images.append(img_path)
                    self.cat_labels[idx].configure(image=photo)
                    self.cat_labels[idx].image = photo
            else:
                idx = len(self.dog_images)
                if idx < len(self.dog_labels):
                    self.dog_images.append(img_path)
                    self.dog_labels[idx].configure(image=photo)
                    self.dog_labels[idx].image = photo
        except Exception as e:
            print(f"Error selecting image {img_path}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PetClassifierApp(root)
    root.mainloop()