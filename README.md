# tec6-programacao_avancada
Repositório referente aos trabalhos da disciplina de Programação Avançada (TEC VI)
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Tabela de Trabalhos</title>
  <style>
    body {
      font-family: Arial, sans-serif;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    th, td {
      border: 1px solid #444;
      padding: 8px;
      text-align: center;
    }
    th {
      background-color: #336699;
      color: white;
    }
    tr:nth-child(even) {
      background-color: #f2f2f2;
    }
    input, select {
      margin: 5px;
      padding: 5px;
    }
    button {
      margin: 5px;
      padding: 5px 10px;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <h2>Tabela de Entregas</h2>

  <div>
    <label>Trabalho: <input type="number" id="trabalho" min="1" max="15"></label>
    <label>Data e hora: <input type="datetime-local" id="datahora"></label>
    <label>Link Git: <input type="url" id="link"></label>
    <label>Status:
      <select id="status">
        <option value="Sim">Sim</option>
        <option value="Não">Não</option>
      </select>
    </label>
    <button onclick="adicionarLinha()">Adicionar/Atualizar</button>
  </div>

  <table id="tabela">
    <thead>
      <tr>
        <th>Trabalho</th>
        <th>Data e hora da entrega do último arquivo</th>
        <th>Link para os arquivos no GIT</th>
        <th>Fez tudo o que foi solicitado e no prazo?</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <script>
    const tabela = document.querySelector("#tabela tbody");

    function adicionarLinha() {
      const trabalho = document.getElementById("trabalho").value;
      const datahora = document.getElementById("datahora").value;
      const link = document.getElementById("link").value;
      const status = document.getElementById("status").value;

      if (!trabalho) return alert("Digite o número do trabalho!");

      let linhaExistente = [...tabela.rows].find(r => r.cells[0].innerText == trabalho);

      if (linhaExistente) {
        linhaExistente.cells[1].innerText = datahora ? new Date(datahora).toLocaleString() : "";
        linhaExistente.cells[2].innerHTML = link ? `<a href="${link}" target="_blank">Repositório</a>` : "";
        linhaExistente.cells[3].innerText = status;
      } else {
        let linha = tabela.insertRow();
        linha.insertCell(0).innerText = trabalho;
        linha.insertCell(1).innerText = datahora ? new Date(datahora).toLocaleString() : "";
        linha.insertCell(2).innerHTML = link ? `<a href="${link}" target="_blank">Repositório</a>` : "";
        linha.insertCell(3).innerText = status;
      }
    }

    // cria linhas vazias até 15
    for (let i = 1; i <= 15; i++) {
      let linha = tabela.insertRow();
      linha.insertCell(0).innerText = i;
      linha.insertCell(1).innerText = "";
      linha.insertCell(2).innerText = "";
      linha.insertCell(3).innerText = "";
    }
  </script>
</body>
</html>
