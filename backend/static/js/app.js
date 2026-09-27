/* RB Prospecta - interações do formulário de campo */
(function () {
  "use strict";

  /* ---------- máscaras ---------- */
  function mascara(valor, padrao) {
    const digitos = valor.replace(/\D/g, "");
    if (padrao === "tel") {
      const d = digitos.slice(0, 11);
      if (d.length <= 2) return d;
      if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
      if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
      return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
    }
    if (padrao === "cpf") {
      const d = digitos.slice(0, 11);
      return d
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
        .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
    }
    if (padrao === "cep") {
      const d = digitos.slice(0, 8);
      return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
    }
    if (padrao === "data") {
      const d = digitos.slice(0, 8);
      if (d.length <= 2) return d;
      if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
      return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
    }
    return valor;
  }

  document.addEventListener("input", (ev) => {
    const campo = ev.target;
    const tipo = campo.dataset && campo.dataset.mask;
    if (tipo) campo.value = mascara(campo.value, tipo);
  });

  /* ---------- linhas dinâmicas ---------- */
  function adicionaLinha(containerId, botaoId, limite, html) {
    const botao = document.getElementById(botaoId);
    if (!botao) return;
    botao.addEventListener("click", () => {
      const container = document.getElementById(containerId);
      if (container.children.length >= limite) {
        botao.style.display = "none";
        return;
      }
      container.insertAdjacentHTML("beforeend", html());
      if (container.children.length >= limite) botao.style.display = "none";
    });
  }

  adicionaLinha("telefones", "add-telefone", 3, () => `
    <div class="linha-removivel">
      <input type="tel" name="telefone" placeholder="(00) 00000-0000" data-mask="tel"
             inputmode="tel" aria-label="Novo telefone">
      <button type="button" class="btn-remove remove-linha" aria-label="Remover telefone">✕</button>
    </div>`);

  adicionaLinha("redes", "add-rede", 3, () => {
    const i = document.querySelectorAll("#redes .rede-linha").length;
    return `
    <div class="rede-linha card-inset">
      <select name="rede_id_${i}" aria-label="Rede social ${i + 1}">
        <option value="">Rede…</option>
        ${Array.from(document.querySelectorAll("#redes select:first-of-type option"))
          .filter((o) => o.value)
          .map((o) => `<option value="${o.value}">${o.text}</option>`)
          .join("")}
      </select>
      <input type="text" name="rede_perfil_${i}" placeholder="@perfil ou link" aria-label="Perfil ${i + 1}">
      <label class="check-inline"><input type="checkbox" name="rede_contato_${i}"> contato</label>
      <label class="check-inline"><input type="checkbox" name="rede_seguir_${i}"> seguir</label>
    </div>`;
  });

  document.addEventListener("click", (ev) => {
    if (ev.target.classList.contains("remove-linha")) {
      ev.target.closest(".linha-removivel").remove();
      const botao = document.getElementById("add-telefone");
      if (botao) botao.style.display = "";
    }
  });

  /* ---------- mostra/esconde bloco de marcas ---------- */
  function sincronizaMarcas() {
    const bloco = document.getElementById("bloco-marcas");
    if (!bloco) return;
    const marcado = document.querySelector('input[name="vende_outras_marcas"]:checked');
    bloco.style.display = marcado && marcado.value === "sim" ? "" : "none";
  }
  document.addEventListener("change", (ev) => {
    if (ev.target.name === "vende_outras_marcas") sincronizaMarcas();
  });
  sincronizaMarcas();
})();
