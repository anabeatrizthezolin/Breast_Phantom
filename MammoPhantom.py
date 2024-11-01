import sys, os, random, time, math, pygame
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian
from tkinter import ttk
from PIL import Image, ImageTk
from scipy.ndimage import gaussian_filter

####################################################################################################
##################################### Formato da mama e mamilo #####################################
####################################################################################################

def main_format(columns, lines, frequency, laterality):
    start_time = time.time()
    
    columns = int(columns)
    lines = int(lines)
    frequency = float(frequency)
    r_contrast = 4095
    background_breast = 200
    background_nipple = random.randint(1600, 1800)
    
    # Criar uma matriz vazia para desenhar a mama
    image = np.full((lines, columns), 0)
    
    # Desenho do mamilo
    
    a = columns * 0.03  # Largura
    b = lines * 0.02  # Altura
    
    for y in range(lines):
        if ((y - lines / 2) ** 2) <= (b ** 2):
            x = np.sqrt((1 - ((y - lines / 2) ** 2) / (b ** 2)) * (a ** 2)) + columns * 0.5
            
            if laterality == 'Esquerda':
                if 0 <= int(x) < columns:
                    image[y, :int(x)] = background_nipple
            elif laterality == "Direita":
                if 0 <= columns - int(x) + a < columns:
                    image[y, columns - int(x):] = background_nipple        
                      
    # Desenho da mama
    a = columns * 0.5  # Largura  
    b = lines * 0.35   # Altura

    for y in range(lines):
        if ((y - lines / 2) ** 2) <= (b ** 2):
            x = np.sqrt((1 - ((y - lines / 2) ** 2) / (b ** 2)) * (a ** 2))
            if laterality == "Esquerda":
                if 0 <= int(x) < columns:
                    image[y, int(x):int(x)+2] = background_nipple
                    image[y, :int(x)] = background_breast  
            elif laterality == "Direita":
                if 0 <= columns - int(x) < columns:
                    image[y, columns - int(x)-2:columns - int(x)] = background_nipple
                    image[y, columns - int(x):] = background_breast
    
    texture(image, columns, lines, background_breast, frequency, r_contrast, laterality, a, start_time)
    
####################################################################################################
##################################### Textura do fundo da mama #####################################
####################################################################################################
    
def s_curve(t):
    return t * t * (3 - (2 * t)) # Função 3t²-2t³

def lerp(t, a, b):
    return a + t * (b - a) # Função de interpolação dos vetores

def setup(k):
    t = k  + B
    b0 = int(t) & (B-1)
    b1 = (b0+1) & (B-1)
    r0 = t - int(t)
    r1 = r0 - 1
    
    return b0, b1, r0, r1
    
def at(rx, ry, q):
    return rx * q[0] + ry * q[1]

def normalize(i, j):
    s = math.sqrt((i * i) + (j * j))
    i = i / s
    j = j / s
    
    return i, j

def init():
    
    for i in range(B):
        p.append(i)
        
        for j in range(2):
            g[i][j] = (random.randint(-B, B) / B)
            
        g[i][0], g[i][1] = normalize(g[i][0], g[i][1])
    
    for i in range(B - 1, 0, -1):
        k = p[i]
        j = random.randint(0, B - 1)
        p[i], p[j] = p[j], k
    
    for i in range(B + 2):
        p.append(p[i])
        for j in range(2):
            g[B + i][j] = g[i][j]
    
def noise2(x, y):
    global start
    if(start):
        start = False
        init()
    
    bx0, bx1, rx0, rx1 = setup(x)
    by0, by1, ry0, ry1 = setup(y)
    
    i = p[bx0]
    j = p[bx1]
    
    b00 = p[i + by0]
    b10 = p[j + by0]
    b01 = p[i + by1]
    b11 = p[j + by1]
    
    sx = s_curve(rx0)
    sy = s_curve(ry0)
    
    q = g[b00]
    u = at(rx0, ry0, q)
    q = g[b10]
    v = at(rx1, ry0, q)
    a = lerp(sx, u, v)
    
    q = g[b01]
    u = at(rx0, ry1, q)
    q = g[b11]
    v = at(rx1, ry1, q)
    b = lerp(sx, u, v)
    
    return lerp(sy, a, b)

def fractal_noise(x, y, octaves, persistence, freq):
    lacunarity = 2
    total_noise = 0
    max_amplitude = 0
    amplitude = 1
    
    for i in range (octaves):
        
        frequency = freq * (lacunarity**i)
        noise_octave = amplitude * (noise2(x * frequency, y * frequency)) 
        
        total_noise += noise_octave
        max_amplitude += amplitude
        amplitude = amplitude * persistence
    
    return total_noise/max_amplitude
    
def texture(image, columns, lines, background_breast, frequency, r_contrast, laterality, a, start_time):

    octaves = 5
    persistence = random.uniform(0.5, 0.8)
    
    for i in range(lines):
        for j in range(columns):
            if image[i][j] == background_breast:
                # Gera o valor de ruído fractal para as coordenadas (i, j)
                fractal_value = fractal_noise(i, j, octaves, persistence, frequency)
                # Normaliza o valor de ruído para o intervalo [0, r_contrast]
                image[i][j] += r_contrast * ((fractal_value + 1) / 2)
    
    main_ducts(image, columns, lines, laterality, a, r_contrast, start_time)
                
#####################################################################################################
##################################### Rede de Ductos Lactíferos #####################################
#####################################################################################################

# Função para desenhar a rede de ductos com ramos de comprimento aleatório
def draw_ducts(surface_ducts, x, y, angle, levels, level_max, min_length, max_length, columns, lines, color_ducts, size, a):
    
    sub_level1 = level_max-2
    sub_level2 = int(level_max*0.7)
    sub_level3 = 2
    
    if(levels == sub_level1):
        min_length = (a*0.05-a*0.05*0.5)
        max_length = (a*0.05+a*0.05*0.1)
    
    if(levels == sub_level2):
        min_length = (a*0.5/(sub_level2-sub_level3)-a*0.5/(sub_level2-sub_level3)*0.7)
        max_length = (a*0.5/(sub_level2-sub_level3)+a*0.5/(sub_level2-sub_level3)*0.8)
        
    if(levels == sub_level3):
        min_length = (a*0.15/sub_level3-a*0.2/sub_level3*0.5)
        max_length = (a*0.15/sub_level3+a*0.2/sub_level3*0.7) 
    
    if(levels == int(lines//1500)):
        size = 1
        
    if levels > 0:
        
        # Define um comprimento aleatório para o ramo
        branch_length = random.uniform(min_length, max_length)
        
        # Calcula a posição final do ramo
        new_x = x + int(branch_length * math.cos(angle))
        new_y = y + int(branch_length * math.sin(angle))
        pygame.draw.line(surface_ducts, color_ducts, (x, y), (new_x, new_y), size)
        draw_ducts(surface_ducts, new_x, new_y, angle - random.uniform(0.1, 0.7), levels - 1, level_max, min_length, max_length, columns, lines, color_ducts, size, a)
        draw_ducts(surface_ducts, new_x, new_y, angle + random.uniform(0.1, 0.7), levels - 1, level_max, min_length, max_length, columns, lines, color_ducts, size, a)

# Função para converter a rede de ductos do pygame para uma matriz
def pygame_surface_to_array(surface_ducts, columns, lines):
    
    surface_array = pygame.surfarray.array3d(surface_ducts)
    
    image_ducts = np.full((lines, columns), 0)
    for i in range(lines):
        for j in range(columns):
            if not np.array_equal(surface_array[i][j], [0, 0, 0]):
                image_ducts[i][j] = int(np.mean(surface_array[i][j]))*4095/255
                
    return image_ducts

def main_ducts(image, columns, lines, laterality, a, r_contrast, start_time):
    
    pygame.init()
    surface_ducts = pygame.Surface((lines, columns), pygame.SRCALPHA)

    color_ducts = (255, 255, 255)

    # Inicia a rede de ductos com comprimento 1
    min_length = 1
    max_length = 1
    
    # Configuração da rede de ductos
    levels = 9 + int(lines//1500) # Quanto maior a imagem/mama, mais níveis de ductos a mama possui
    sigma = 1.4 + int(lines//600) # Quanto maior a imagem/mama, maior o borramento dos ductos
    size = 1 + int(lines/1700)
    
    # Ângulo do crescimento da rede - depende da lateralidade da imagem
    if(laterality == "Direita"):
        angle = math.pi/2
        x = lines/2
        y = columns-a
    else:
        angle = 3*math.pi/2
        x = lines/2
        y = a
    
    draw_ducts(surface_ducts, x, y, angle, levels, levels, min_length, max_length, columns, lines, color_ducts, size, a)

    image_ducts = pygame_surface_to_array(surface_ducts, columns, lines)

    # Filtro gaussiano para desfocar a rede de ductos para aparência mais natural
    image_ducts = gaussian_filter(image_ducts, sigma)

    image = add_ducts(image, image_ducts, columns, lines)
    pygame.quit()
    
    result(image, r_contrast, start_time) 

def add_ducts(image, image_ducts, columns, lines):

    for i in range(lines):
        for j in range(columns):
            if(not np.array_equal(image_ducts[i][j], [0, 0, 0]) and image[i][j] != 0):
                image[i][j] += image_ducts[i][j]/4
    return image

#####################################################################################
##################################### Interface #####################################
#####################################################################################

def get_percentage_height(percent):
    percent = int((percent / 100) * s_height)
    return percent

def input_validation(input, columns, lines, frequency, laterality, line_label, column_label, frequency_label):
    global linec_label, columnc_label, frequencyc_label
    if(lines.get() == "Ex: 2150" or int(lines.get()) == 0):
        l_error = True
    else: 
        l_error = False

    if(columns.get() == "Ex: 1765" or int(columns.get()) == 0):
        c_error = True
    else: 
        c_error = False
    
    if(frequency.get()  == "Ex: 0.01" or float(frequency.get()) == 0.0):
        f_error = True
    else: 
        f_error = False
    
    if(c_error == True or l_error == True or f_error == True):
        new_input(input, c_error, l_error, f_error)
    else: clear(columns, lines, frequency, laterality)

def clear(column, line, freq, lat):
    
    columns = column.get()
    lines = line.get()
    frequency = freq.get()
    laterality = lat.get()
    
    column.delete(0, "end")
    entry_suggestion(column, "Ex: 1765")
    line.delete(0, "end")
    entry_suggestion(line, "Ex: 2150")
    freq.delete(0, "end")
    entry_suggestion(freq, "Ex: 0.01")
    
    main_format(columns, lines, frequency, laterality)
    
def new_input(input, c_error, l_error, f_error):
    global linec_label, columnc_label, frequencyc_label
    
    if(l_error == True):
        linec_label = tk.Label(input, text="*Campo vazio ou inválido", bg="#fd4d79", font=("Gayathri",9)).grid(row=2, column=1, pady=5)
        tk.Label(input, text="", bg="#fd4d79", font=("Gayathri", 9)).grid(row=2, column=2, pady=5)

    if(c_error == True):
        columnc_label = tk.Label(input, text="*Campo vazio ou inválido", bg="#fd4d79", font=("Gayathri", 9)).grid(row=2, column=3, pady=5)
    
    if(f_error == True):
        frequencyc_label = tk.Label(input, text="*Campo vazio ou inválido", bg="#fd4d79", font=("Gayathri", 9)).grid(row=4, column=1, columnspan=3, pady=5)
    
def result(image, r_contrast, start_time):
 
    for widget in frame.winfo_children():
        widget.destroy() 
        
    plt.imsave(os.path.join(path, "Mama.png"), image, cmap='gray', vmin=0, vmax=r_contrast)
        
    result_screen = tk.Frame(frame, bg="#ffb3c6")
    result_screen.pack(fill=tk.BOTH, expand=True)
    
    title_label = tk.Label(result_screen, text="MammoPhantom", bg="#ffb3c6", font=("Gayathri", 26), fg="black")
    title_label.pack(pady=10)

    image_png = Image.open(os.path.join(path, "Mama.png"))

    image_width, image_height = image_png.size

    screen_width = screen.winfo_screenwidth()
    screen_height = screen.winfo_screenheight()

    # Tamanho máximo baseado na proporção da tela
    max_size = int(min(screen_width, screen_height) * 0.6)
    
    # Calcula as novas dimensões mantendo a proporção
    if image_width > image_height:
        new_width = max_size
        new_height = int((max_size / image_width) * image_height)
    else:
        new_height = max_size
        new_width = int((max_size / image_height) * image_width)

    # Redimensiona a imagem
    image_png = image_png.resize((new_width, new_height), Image.LANCZOS)

    os.remove('Mama.png')
    global start
    start = True
    
    photo = ImageTk.PhotoImage(image_png)
    label = tk.Label(result_screen, image=photo, bg="white")
    label.photo = photo
    label.pack(expand=True)
    
    end_time = time.time()
    time_total = end_time-start_time
    
    time_label = tk.Label(result_screen, text=f"Tempo de execução: {time_total:.5f} segundos", bg="#ffb3c6", font=("Gayathri", 12), fg="black")
    time_label.pack(pady = 10)
    
    name = tk.Entry(result_screen, width=18)
    name.pack()
    entry_suggestion(name, "Nome do arquivo")
    
    save_button = tk.Button(result_screen, text="Salvar", bg="white", font=("Gayathri", 16), command=lambda: save(image, name.get(), name))
    save_button.pack(pady = 10)

def save(image, name_image, name):
    
    name.delete(0, "end")
    entry_suggestion(name, "Nome do arquivo")
    
    # Criação do Dataset principal
    ds = Dataset()
    
    if image.max() > 4095:
        image = np.clip(image, 0, 4095)  # Garante valores no intervalo permitido para 12 bits

    # Configuração das dimensões e dados da imagem
    ds.Rows, ds.Columns = image.shape
    ds.PixelData = image.astype(np.uint16).tobytes()  # Converte para 16 bits se necessário
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16 
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0  # 0 para dados não assinados

    # Criação e configuração do FileMetaDataset
    file_meta = FileMetaDataset()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds.file_meta = file_meta

    # Caminho e o nome do arquivo DICOM
    caminho = os.path.join(path, "Generated images")
    output_image = os.path.join(caminho, name_image + ".dcm")
    ds.save_as(output_image)

def validate_numeric_point_input(text, placeholder_text):
    # Permite números ou a sugestão
    if text == placeholder_text:
        return True
    # Permite apenas números e ponto
    elif text == "" or all(char.isdigit() or char in "." for char in text):
        # Permite apenas 1 ponto
        if text.count(".") <= 1:
            return True
    return False

def validate_numeric_input(text, placeholder_text):
    return text.isdigit() or text == "" or text == placeholder_text

def entry_suggestion(entry, placeholder_text):
    
    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.config(fg='grey')
    
    entry.insert(0, placeholder_text)
    entry.config(fg='grey')

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

def main_screen():
    
    # Apagar tela
    for widget in frame.winfo_children():
        widget.destroy() 
        
    main = tk.Frame(frame, bg="#ffb3c6")
    main.pack(pady=size_column)
    
    title_start = tk.Label(main, text="MammoPhantom", bg="#ffb3c6", font=("Gayathri", 28), fg="black")
    title_start.grid(row=0, column=0, columnspan=2, pady=get_percentage_height(5))  
    
    input = tk.Frame(screen, bg="#fd4d79", width=size_column)
    input.grid(row=0, column=0, sticky="n")
    
    # Adicionando os campos de entrada
    tk.Label(input, text="", bg="#fd4d79", font=("Gayathri", 14)).grid(row=0, column=0, pady=15, sticky="w")
    
    tk.Label(input, text="Resolução espacial:", bg="#fd4d79", font=("Gayathri", 15)).grid(row=1, column=0, pady=10, padx=5, sticky="w")
    lines = tk.Entry(input, width=10, font=("Gayathri", 13), validate="key", validatecommand=(screen.register(validate_numeric_input), "%P", "Ex: 2150"))
    lines.grid(row=1, column=1, pady=10, padx=15, sticky='w')
    entry_suggestion(lines, "Ex: 2150")
    line_label = tk.Label(input, text=" ", bg="#fd4d79", font=("Gayathri", 9))
    line_label.grid(row=2, column=1, pady=5, sticky="w")
    
    tk.Label(input, text="x", bg="#fd4d79", font=("Gayathri", 14)).grid(row=1, column=2)
    columns = tk.Entry(input, width=10, font=("Gayathri", 13), validate="key", validatecommand=(screen.register(validate_numeric_input), "%P", "Ex: 1765"))
    columns.grid(row=1, column=3, pady=10, padx=15)
    entry_suggestion(columns, "Ex: 1765")
    column_label = tk.Label(input, text=" ", bg="#fd4d79", font=("Gayathri", 9))
    column_label.grid(row=2, column=3, pady=5, sticky="w")
    
    tk.Label(input, text="Frequência:", bg="#fd4d79", font=("Gayathri", 15)).grid(row=3, column=0, pady=10, padx=5, sticky="w")
    frequency = tk.Entry(input, width=10, font=("Gayathri", 13), validate="key", validatecommand=(screen.register(validate_numeric_point_input), "%P", "Ex: 0.01"))
    frequency.grid(row=3, column=1, columnspan=3, pady=10, padx=15)
    entry_suggestion(frequency, "Ex: 0.01")
    frequency_label = tk.Label(input, text=" ", bg="#fd4d79", font=("Gayathri", 9))
    frequency_label.grid(row=4, column=1, pady=5, sticky="w")
    
    lateralitys = ["Direita", "Esquerda"]
    tk.Label(input, text="Lateralidade da imagem:", bg="#fd4d79", font=("Gayathri", 15)).grid(row=5, column=0, pady=10, padx=5, sticky="w")
    laterality_combobox = ttk.Combobox(input, values=lateralitys, font=("Gayathri", 14), state="readonly", width=size_button)
    laterality_combobox.current(0)
    laterality_combobox.grid(row=5, column=1, columnspan=3, pady=10, padx=15)
    laterality_combobox.bind("<KeyRelease>", lateralitys)
    
    tk.Label(input, text=" ", bg="#fd4d79", font=("Gayathri", 9)).grid(row=6, column=1, pady=5, sticky="w")
    
    process_button = tk.Button(input, text="Gerar", bg="white", font=("Gayathri", 16), command=lambda: input_validation(input, columns, lines, frequency, laterality_combobox, line_label, column_label, frequency_label))
    process_button.grid(row=7, column=0, columnspan=4, pady=20, padx=14)
    
    image = Image.open(os.path.join(path, "LogoGIM.png"))
    image = image.resize((166,188), Image.LANCZOS)
    
    photo = ImageTk.PhotoImage(image)
    label = tk.Label(input, image=photo, bg="white")
    label.photo = photo
    label.grid(row=9, column=0, columnspan=4, pady=70, sticky="n")

screen = tk.Tk()
screen.title("MammoPhantom")
screen.configure(bg="#ffb3c6")  # Cor do fundo
s_width = screen.winfo_screenwidth()  # Largura da tela
s_height = screen.winfo_screenheight()  # Altura da tela
screen.geometry(f"{s_width}x{s_height}")

B = 4096
NP = 12
p = [] # Vetor de permtações vazio
g = [[0, 0] for _ in range(B + B + 2)]  # Vetor de gradientes vazio
color_ducts = (255,255,255)
start = True

path = os.path.split(sys.argv[0])[0]
size_button = 10  # Indica o tamanho dos botões
size_column = get_percentage_height(35)

screen.columnconfigure(0, minsize=size_button)

frame = tk.Frame(screen, bg="#ffb3c6", width=size_column)
frame.grid(row=0, column=1, rowspan=4, sticky="nsew")
screen.grid_rowconfigure(0, weight=1)
screen.grid_columnconfigure(1, weight=1)

title_start = tk.Label(frame, text="Bem-vindo ao MammoPhantom", bg="#ffb3c6", font=("Gayathri", 30), fg="black")
title_start.pack(expand=True)

start_button = tk.Button(frame, text="Iniciar", bg="#fd4d79", command=main_screen, font=("Gayathri", 18), width=10, fg="black")
start_button.pack(expand=True)
# Executa
screen.mainloop()
