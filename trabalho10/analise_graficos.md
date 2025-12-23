# Análise dos gráficos gerados
## Resumo
Ao comparar a execução dos dois algoritmos de busca, pode-se notar a diferença das velocidades, mesmo aplicando a mesma lógica de mudança de velocidade aleatória de agentes para ambos. O algoritmo A* percorre o caminho de origem a destino com muito mais rapidez que o DFS, considerando que não percorre uma quantidade considerável de nós, por buscar a eficiência. Além da rapidez, é notável a maior latência de processamento do algoritmo DFS, também reafirmada por sua maior expansão de caminhos. Nos próximos trabalhos irei focar as execuções em A* por melhor otimização.
Ao se tratar da diferença de geometria dos grids, a diferência é irrisória, logo ambos são boas opções de geometria para futuras aplicações.
Abaixo estão os gráficos plotados com base no arquivo log gerado por cada diferente execução.

### A* em grid retangular
<img width="1984" height="572" alt="image" src="https://github.com/user-attachments/assets/517c053a-b07c-4af5-be17-5c1fc33c7657" />


### A* em grid hexagonal
<img width="1984" height="572" alt="image" src="https://github.com/user-attachments/assets/75354bdc-4f54-44c9-8c5b-47e0e58dc43f" />


### DFS em grid retangular
<img width="1984" height="572" alt="image" src="https://github.com/user-attachments/assets/e2c60f38-a1aa-474f-8f2d-b4ddc1004a12" />


### DFS em grid hexagonal
<img width="1984" height="572" alt="image" src="https://github.com/user-attachments/assets/1029bb9e-0dba-4c2a-af86-a8c35d8d009e" />
