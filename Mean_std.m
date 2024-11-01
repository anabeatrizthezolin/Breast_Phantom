clc;

pkg load dicom; % Carrega o pacote de manipulação de imagem DICOM

num_images = 20; % Número de imagens
mean_total = 0;
std_total = 0;

output_file = fopen('Results_mean_std_simulation.txt', 'w');
fprintf(output_file, 'Mean\tStandard deviation\n'); % Cabeçalho do arquivo

for i = 1:num_images
    name_im = ['/home/anabeatriz/Área de Trabalho/TCC/MammoPhantom/Test_simulation/Teste' num2str(i) '.dcm'];
    im_in = dicomread (name_im); % Lê a imagem e a converte em matriz

    % Cálculo da média e do desvio padrão da imagem atual
    mean_image = mean(im_in(:)); 
    std_image = std(im_in(:));

    fprintf(output_file, '%.2f\t%.2f\n', mean_image, std_image);
    
    mean_total = mean_total + mean_image; 
    std_total = std_total + std_image;
end

fprintf(output_file, '\nMean: %.2f\n', mean_total / num_images);
fprintf(output_file, 'Standard deviation: %.2f\n', std_total / num_images);

fclose(output_file);

fprintf('Média das imagens: %.2f\n', mean_total / num_images);
fprintf('Desvio padrão das imagens: %.2f\n', std_total / num_images);
