# Análise dos gráficos gerados
## Resumo:
Ao gerar gráficos de desempenho referentes aos três tipos de navegação, é possível perceber que tanto a navegação com comunicação direta quanto a sem comunicação possuem tamanho de caminho e tempo de execução bastante similares, mesmo se tratando de abordagem bastante distintas. Porém, é possível apontar que a melhor opção ao observar o custo computacional, a navegação sem comunicação utilizando o algoritmo ORCA. 

Por outro lado, considerando o custo computacional dos algoritmos, é evidente que a navegação com comunicação indireta teria o menor valor por se tratar de uma opção mais simples; mesmo assim, acaba tendo caminho e tempo de execução consideravelmente maiores que as outras duas abordagens.

Portanto, mesmo sendo necessário aplicar um algoritmo externo ao código base, o método de navegação sem comunicação entre os agentes é o mais adequado levando em consideração o desempenho e a qualidade da abordagem.


## Gráficos
### Tamanho médio do caminho
<img width="1006" height="557" alt="image" src="https://github.com/user-attachments/assets/84e7542b-f832-4882-b858-bd65b5999ca3" />



### Distribuição do tempo de execução em milissegundos
<img width="1006" height="557" alt="image" src="https://github.com/user-attachments/assets/7c9493c8-8342-4f43-92bd-6c12121b8660" />



### Total de nós explorados - Custo computacional
<img width="1045" height="558" alt="image" src="https://github.com/user-attachments/assets/0afaed39-ba6d-4dd1-8eac-357e546cd8e0" />
