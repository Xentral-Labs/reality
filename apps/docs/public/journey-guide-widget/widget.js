(function () {
  "use strict";

  const script = document.currentScript;
  if (!script || document.querySelector("reality-journey-chat")) return;
  const apiUrl = (script.dataset.apiUrl || "http://localhost:8000").replace(/\/$/u, "");
  const guideUrl = (script.dataset.guideUrl || "/getting-started/business-journeys").replace(
    /\/$/u,
    "",
  );
  const locale = ["de", "nl", "es"].includes(script.dataset.locale) ? script.dataset.locale : "en";
  const apiLocale = locale;
  const copy =
    locale === "de"
      ? {
          label: "Reality fragen",
          heading: "Was kann Reality?",
          intro:
            "Frage nach einem Geschäftsablauf. Dieser öffentliche Chat sieht keine Unternehmensdaten.",
          placeholder: "Stelle eine Frage zu Reality …",
          followUpPlaceholder: "Stelle eine Rückfrage zu dieser Antwort …",
          newChat: "Neuer Chat",
          send: "Senden",
          close: "Chat schließen",
          wait: "Antwort wird vorbereitet",
          accepted: "Frage wird eingeordnet",
          researching: "Passende Produktquellen werden geprüft",
          composing: "Antwort wird vorbereitet",
          validating: "Aussagen werden belegt",
          unavailable: "Die Antwort ist gerade nicht verfügbar. Öffne den Business Journey Guide.",
          guide: "Im Guide ansehen",
          openJourney: "Journey {id} in neuem Tab öffnen",
          examplesTitle: "Zum Beispiel",
          sources: "Quellen im Business Journey Guide",
          references: "Weitere Produktquellen",
          examples: [
            "Wie bilde ich einen B2B-Auftrag ab?",
            "Was passiert bei einer Teillieferung?",
            "Wie erfasse ich eine Lieferantenrechnung?",
            "Wie erklärt Reality offene Mengen?",
          ],
        }
      : locale === "nl"
        ? {
            label: "Vraag Reality",
            heading: "Wat kan Reality?",
            intro: "Vraag naar een bedrijfsproces. Deze openbare chat ziet geen bedrijfsgegevens.",
            placeholder: "Stel een vraag over Reality …",
            followUpPlaceholder: "Stel een vervolgvraag over dit antwoord …",
            newChat: "Nieuwe chat",
            send: "Versturen",
            close: "Chat sluiten",
            wait: "Antwoord wordt voorbereid",
            accepted: "De vraag wordt beoordeeld",
            researching: "Productbronnen worden gecontroleerd",
            composing: "Het antwoord wordt voorbereid",
            validating: "Beweringen worden onderbouwd",
            unavailable: "Het antwoord is nu niet beschikbaar. Open de Business Journey Guide.",
            guide: "Openen in de Guide",
            openJourney: "Journey {id} openen in een nieuw tabblad",
            examplesTitle: "Bijvoorbeeld",
            sources: "Bronnen in de Business Journey Guide",
            references: "Andere productbronnen",
            examples: [
              "Hoe verwerk ik een B2B-order?",
              "Wat gebeurt er bij een deellevering?",
              "Hoe boek ik een leveranciersfactuur?",
            ],
          }
        : locale === "es"
          ? {
              label: "Preguntar a Reality",
              heading: "¿Qué puede hacer Reality?",
              intro:
                "Pregunta por un proceso empresarial. Este chat público no ve datos de empresas.",
              placeholder: "Haz una pregunta sobre Reality …",
              followUpPlaceholder: "Haz una pregunta sobre esta respuesta …",
              newChat: "Nuevo chat",
              send: "Enviar",
              close: "Cerrar chat",
              wait: "Preparando la respuesta",
              accepted: "Analizando la pregunta",
              researching: "Comprobando fuentes del producto",
              composing: "Preparando la respuesta",
              validating: "Validando las afirmaciones",
              unavailable: "La respuesta no está disponible ahora. Abre la Business Journey Guide.",
              guide: "Abrir en la Guide",
              openJourney: "Abrir journey {id} en una pestaña nueva",
              examplesTitle: "Por ejemplo",
              sources: "Fuentes en la Business Journey Guide",
              references: "Otras fuentes del producto",
              examples: [
                "¿Cómo gestiono un pedido B2B?",
                "¿Qué ocurre con una entrega parcial?",
                "¿Cómo registro una factura de proveedor?",
              ],
            }
          : {
              label: "Ask Reality",
              heading: "What can Reality do?",
              intro: "Ask about a business process. This public chat cannot see company data.",
              placeholder: "Ask a question about Reality …",
              followUpPlaceholder: "Ask a follow-up about this answer …",
              newChat: "New chat",
              send: "Send",
              close: "Close chat",
              wait: "Preparing the answer",
              accepted: "Understanding the question",
              researching: "Checking relevant product sources",
              composing: "Preparing the answer",
              validating: "Checking the answer against sources",
              unavailable: "The answer is unavailable right now. Open the Business Journey Guide.",
              guide: "Open in the Guide",
              openJourney: "Open journey {id} in a new tab",
              examplesTitle: "For example",
              sources: "Sources in the Business Journey Guide",
              references: "Additional product sources",
              examples: [
                "How do I run a B2B order?",
                "What happens with a partial delivery?",
                "How do I record a supplier invoice?",
              ],
            };

  class RealityJourneyChat extends HTMLElement {
    constructor() {
      super();
      const root = this.attachShadow({ mode: "open" });
      root.innerHTML = `
        <style>
          :host{position:fixed;right:24px;bottom:24px;z-index:2147483000;font:15px/1.55 Inter,ui-sans-serif,system-ui,sans-serif;color:#161928}
          *,*::before,*::after{box-sizing:border-box}button,textarea{font:inherit}.launcher{display:flex;align-items:center;gap:9px;border:0;border-radius:999px;padding:13px 19px;background:#6755f5;color:#fff;font-weight:760;box-shadow:0 14px 38px #25214c4d;cursor:pointer}.launcher-mark{font-size:18px;line-height:1}
          .panel{display:none;position:fixed;right:24px;bottom:24px;width:min(640px,calc(100vw - 48px));height:calc(100vh - 48px);height:calc(100dvh - 48px);grid-template-rows:auto minmax(0,1fr) auto;overflow:hidden;border:1px solid #d9ddea;border-radius:24px;background:#fff;box-shadow:0 28px 90px #11182740}
          .panel[data-open=true]{display:grid}.head{display:flex;align-items:start;justify-content:space-between;gap:24px;padding:24px 26px 20px;border-bottom:1px solid #e8eaf2;background:#fff}.head h2{margin:0;font-size:23px;line-height:1.2;letter-spacing:-.02em}.head p{max-width:48ch;margin:8px 0 0;color:#626a7f;font-size:14px}.head-actions{display:flex;align-items:center;gap:8px}.new-chat,.close{min-height:38px;border:0;border-radius:12px;background:#f3f4f8;cursor:pointer;color:#626a7f}.new-chat{padding:0 12px;font-size:13px;font-weight:750;white-space:nowrap}.new-chat[hidden]{display:none}.close{display:grid;place-items:center;flex:0 0 auto;width:38px;font-size:25px;line-height:1}
          .conversation{display:flex;flex-direction:column;gap:14px;min-height:0;padding:22px 24px;overflow-y:auto;overscroll-behavior:contain;background:#fbfbfd;scrollbar-gutter:stable}.message{max-width:88%;font-size:15px;line-height:1.55}.message.user{align-self:flex-end;padding:11px 15px;border-radius:18px 18px 5px 18px;background:#6755f5;color:#fff;line-height:1.45}.message.assistant{align-self:flex-start;width:100%}.answer{padding:16px 18px;border:1px solid #e7e4fa;border-radius:18px 18px 18px 5px;background:#f5f3ff;animation:rjc-answer-in .22s ease-out}.answer p{margin:0 0 10px}.answer p:last-child{margin-bottom:0}.answer .section-title{margin:14px 0 6px;color:#3f348f;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.answer .section-title:first-child{margin-top:0}.answer ul{margin:0 0 10px;padding-left:20px}.answer li{margin:3px 0;padding-left:2px}.answer a{color:#5745df;font-weight:700}.pending{display:flex;align-items:center;gap:11px;width:auto!important;min-height:32px;padding:4px 2px;border:0;background:transparent}.pending-mark{display:grid;place-items:center;width:22px;height:22px;color:#6755f5}.pending-copy{font-size:13px;font-weight:600;color:#625a8f;transition:opacity .16s ease}.typing-dots{display:inline-flex;gap:4px}.typing-dots i{width:5px;height:5px;border-radius:50%;background:currentColor;animation:rjc-pulse 1.2s infinite ease-in-out}.typing-dots i:nth-child(2){animation-delay:.15s}.typing-dots i:nth-child(3){animation-delay:.3s}@keyframes rjc-pulse{0%,70%,100%{opacity:.22;transform:translateY(0) scale(.9)}35%{opacity:1;transform:translateY(-2px) scale(1)}}@keyframes rjc-answer-in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}.examples{margin:auto 0;color:#626a7f}.examples p{margin:0 0 12px;font-size:14px;font-weight:700}.example-list{display:flex;flex-wrap:wrap;gap:9px}.example-list button{border:1px solid #ded9fb;border-radius:999px;padding:9px 13px;background:#fff;color:#4f43c8;cursor:pointer;text-align:left;transition:background .15s,border-color .15s,transform .15s}.example-list button:hover{border-color:#a99cff;background:#f5f3ff;transform:translateY(-1px)}.example-list button:active{transform:translateY(0)}.citations{width:100%;margin-top:14px;padding-top:9px;border-top:1px solid #ded9fb;border-collapse:collapse;table-layout:fixed}.citations tr+tr{border-top:1px solid #e8e4fb}.citations td{padding:4px;font-size:12px;line-height:1.35}.citation-id{width:45px;color:#5144d9;font-weight:800}.citation-title{overflow:hidden;color:#625a8f;font-weight:600;text-overflow:ellipsis;white-space:nowrap}.citation-open{width:27px;text-align:right}.citation-open a{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:7px;text-decoration:none}.citation-open a:hover{background:#e7e2ff}
          .references{margin:14px 0 0!important;padding-top:10px!important;border-top:1px solid #ded9fb;font-size:12px}.references-label{display:block;margin-bottom:5px;color:#625a8f}.references li{margin:2px 0!important}
          form{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:10px;padding:16px 18px 18px;border-top:1px solid #e8eaf2;background:#fff}textarea{min-width:0;max-height:140px;resize:none;padding:13px 15px;border:1px solid #cdd2df;border-radius:14px;background:#fff;color:inherit;line-height:1.45}form button{min-height:48px;border:0;border-radius:14px;padding:11px 18px;background:#6755f5;color:#fff;font-weight:750;cursor:pointer}form button:disabled{opacity:.55;cursor:wait}
          button:focus-visible,textarea:focus-visible,a:focus-visible{outline:3px solid #a99cff;outline-offset:2px}
          @media(max-width:700px){:host{right:14px;bottom:14px}.panel{right:0;bottom:0;width:100%;height:min(82dvh,760px);border-width:1px 0 0;border-radius:24px 24px 0 0}.head{padding:20px}.conversation{padding:16px}.message{max-width:94%;font-size:14px;line-height:1.5}.answer{padding:14px 15px}form{padding:12px}.launcher{padding:12px 16px}}
          @media(prefers-reduced-motion:reduce){.typing-dots i,.answer{animation:none}.pending-copy,.example-list button{transition:none}}@media(prefers-color-scheme:dark){:host{color:#f5f6f8}.panel,.head,form{background:#101828;border-color:#344054}.head p,.examples{color:#98a2b3}.new-chat,.close{background:#1d2939;color:#d0d5dd}.conversation{background:#0c111d}.answer{background:#1d2939;border-color:#344054}.pending{background:transparent}.pending-copy{color:#b4adcf}.example-list button{background:#1d2939;border-color:#475467;color:#d9d4ff}.citations,.citations tr+tr{border-color:#475467}.citation-id,.citation-open a{color:#b8afff}.citation-title{color:#c8c3ef}textarea{background:#101828;border-color:#475467;color:#f5f6f8}}
        </style>
        <button class="launcher" type="button" aria-haspopup="dialog" aria-expanded="false"><span class="launcher-mark" aria-hidden="true">✦</span>${copy.label}</button>
        <section class="panel" role="dialog" aria-modal="false" aria-labelledby="rjc-title" data-open="false">
          <header class="head"><div><h2 id="rjc-title">${copy.heading}</h2><p>${copy.intro}</p></div><div class="head-actions"><button class="new-chat" type="button" hidden>${copy.newChat}</button><button class="close" type="button" aria-label="${copy.close}">×</button></div></header>
          <div class="conversation" aria-live="polite"><div class="examples"><p>${copy.examplesTitle}</p><div class="example-list">${copy.examples.map((question) => `<button type="button">${question}</button>`).join("")}</div></div></div>
          <form><textarea rows="1" maxlength="1000" required aria-label="${copy.placeholder}" placeholder="${copy.placeholder}"></textarea><button type="submit">${copy.send}</button></form>
        </section>`;
      this.launcher = root.querySelector(".launcher");
      this.panel = root.querySelector(".panel");
      this.closeButton = root.querySelector(".close");
      this.newChatButton = root.querySelector(".new-chat");
      this.form = root.querySelector("form");
      this.input = root.querySelector("textarea");
      this.conversation = root.querySelector(".conversation");
      this.sendButton = root.querySelector('form button[type="submit"]');
      this.examples = root.querySelector(".examples");
      this.history = [];
      this.activeController = null;
    }

    connectedCallback() {
      this.launcher.addEventListener("click", () => this.open());
      this.closeButton.addEventListener("click", () => this.close());
      this.newChatButton.addEventListener("click", () => this.resetConversation());
      this.form.addEventListener("submit", (event) => this.ask(event));
      this.shadowRoot.querySelectorAll(".example-list button").forEach((button) => {
        button.addEventListener("click", () => {
          this.input.value = button.textContent;
          this.form.requestSubmit();
        });
      });
      this.input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          this.form.requestSubmit();
        }
      });
      this.addEventListener("keydown", (event) => {
        if (event.key === "Escape") this.close();
      });
    }

    open() {
      this.panel.dataset.open = "true";
      this.launcher.setAttribute("aria-expanded", "true");
      this.input.focus();
    }

    close() {
      this.activeController?.abort();
      this.panel.dataset.open = "false";
      this.launcher.setAttribute("aria-expanded", "false");
      this.launcher.focus();
    }

    resetConversation() {
      this.activeController?.abort();
      this.history = [];
      this.conversation.replaceChildren(this.examples);
      this.newChatButton.hidden = true;
      this.input.value = "";
      this.input.placeholder = copy.placeholder;
      this.input.setAttribute("aria-label", copy.placeholder);
      this.input.focus();
    }

    async ask(event) {
      event.preventDefault();
      const question = this.input.value.trim();
      if (!question) return;
      this.examples?.remove();
      this.newChatButton.hidden = false;
      this.appendUserMessage(question);
      this.input.value = "";
      this.input.disabled = true;
      this.sendButton.disabled = true;
      const pending = document.createElement("div");
      pending.className = "message assistant pending";
      pending.setAttribute("role", "status");
      pending.setAttribute("aria-label", copy.wait);
      const dots = document.createElement("span");
      dots.className = "pending-mark typing-dots";
      dots.setAttribute("aria-hidden", "true");
      dots.append(
        document.createElement("i"),
        document.createElement("i"),
        document.createElement("i"),
      );
      pending.append(dots);
      const pendingCopy = document.createElement("span");
      pendingCopy.className = "pending-copy";
      pendingCopy.textContent = copy.accepted;
      pending.append(pendingCopy);
      this.conversation.append(pending);
      this.scrollConversation();
      const controller = new AbortController();
      this.activeController = controller;
      const timeout = setTimeout(() => controller.abort(), 40000);
      try {
        const response = await fetch(`${apiUrl}/api/journey-guide/questions?stream=true`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, locale: apiLocale, history: this.history }),
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("journey question unavailable");
        if (!response.body) throw new Error("journey progress unavailable");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let answer = null;
        while (true) {
          const { value, done } = await reader.read();
          buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (!line.trim()) continue;
            const event = JSON.parse(line);
            if (event.stage === "complete") {
              answer = event.answer;
            } else if (copy[event.stage]) {
              pendingCopy.textContent = copy[event.stage];
              pending.setAttribute("aria-label", copy[event.stage]);
            }
          }
          if (done) break;
        }
        if (!answer) throw new Error("journey progress incomplete");
        pending.remove();
        this.show(answer);
        this.history.push(
          { role: "user", content: question },
          { role: "assistant", content: answer.text },
        );
        this.history = this.history.slice(-20);
      } catch (_error) {
        pending.remove();
        if (!controller.signal.aborted) {
          const message = document.createElement("div");
          message.className = "message assistant answer";
          const paragraph = document.createElement("p");
          paragraph.textContent = copy.unavailable;
          const link = document.createElement("a");
          link.href = guideUrl;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.textContent = copy.guide;
          message.append(paragraph, link);
          this.conversation.append(message);
          this.scrollConversation();
        }
      } finally {
        clearTimeout(timeout);
        if (this.activeController === controller) this.activeController = null;
        this.input.disabled = false;
        this.sendButton.disabled = false;
        this.input.focus();
      }
    }

    appendUserMessage(question) {
      const message = document.createElement("div");
      message.className = "message user";
      message.textContent = question;
      this.conversation.append(message);
    }

    appendInlineFormatted(container, text) {
      const parts = text.split(/(\*\*[^*]+\*\*)/u);
      for (const part of parts) {
        if (part.startsWith("**") && part.endsWith("**")) {
          const strong = document.createElement("strong");
          strong.textContent = part.slice(2, -2);
          container.append(strong);
        } else {
          container.append(document.createTextNode(part));
        }
      }
    }

    appendFormattedText(container, text) {
      const structured = String(text).replace(
        /\s+\*\*(So geht(?: es)?|Praktischer Workflow|Tools|Grenze|Wichtige Lücke):?\*\*\s*/giu,
        "\n\n**$1**\n\n",
      );
      for (const block of structured.split(/\n{2,}/u)) {
        const lines = block.split("\n").filter((line) => line.trim());
        if (lines.length === 1 && /^\*\*[^*]+\*\*$/u.test(lines[0].trim())) {
          const heading = document.createElement("h3");
          heading.className = "section-title";
          heading.textContent = lines[0].trim().slice(2, -2).replace(/:$/u, "");
          container.append(heading);
          continue;
        }
        if (lines.every((line) => /^[-•]\s+/u.test(line.trim()))) {
          const list = document.createElement("ul");
          for (const line of lines) {
            const item = document.createElement("li");
            this.appendInlineFormatted(item, line.trim().replace(/^[-•]\s+/u, ""));
            list.append(item);
          }
          container.append(list);
          continue;
        }
        const paragraph = document.createElement("p");
        this.appendInlineFormatted(paragraph, lines.join(" "));
        container.append(paragraph);
      }
    }

    scrollConversation() {
      this.conversation.scrollTop = this.conversation.scrollHeight;
    }

    scrollAnswerToStart(box) {
      this.conversation.scrollTop = Math.max(0, box.offsetTop - this.conversation.offsetTop - 12);
    }

    show(answer) {
      this.input.placeholder = copy.followUpPlaceholder;
      this.input.setAttribute("aria-label", copy.followUpPlaceholder);
      const box = document.createElement("div");
      box.className = "message assistant answer";
      this.appendFormattedText(box, answer.text);
      const citations = document.createElement("table");
      citations.className = "citations";
      citations.setAttribute("aria-label", copy.sources);
      const citationBody = document.createElement("tbody");
      const matches = new Map((answer.matches || []).map((match) => [match.id, match]));
      for (const id of answer.citations || []) {
        const row = document.createElement("tr");
        const idCell = document.createElement("td");
        idCell.className = "citation-id";
        idCell.textContent = id;
        const titleCell = document.createElement("td");
        titleCell.className = "citation-title";
        titleCell.textContent = matches.get(id)?.title || "Journey";
        titleCell.title = matches.get(id)?.title || id;
        const openCell = document.createElement("td");
        openCell.className = "citation-open";
        const link = document.createElement("a");
        link.href = `${guideUrl}#${encodeURIComponent(id)}`;
        link.textContent = "↗";
        link.title = matches.get(id)?.title || id;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.setAttribute("aria-label", copy.openJourney.replace("{id}", id));
        openCell.append(link);
        row.append(idCell, titleCell, openCell);
        citationBody.append(row);
      }
      citations.append(citationBody);
      box.append(citations);
      const publicSources = (answer.sources || []).filter((source) => source.url);
      if (publicSources.length) {
        const references = document.createElement("ul");
        references.className = "references";
        const label = document.createElement("strong");
        label.className = "references-label";
        label.textContent = copy.references;
        references.append(label);
        for (const source of publicSources) {
          const item = document.createElement("li");
          const link = document.createElement("a");
          link.href = source.url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.textContent = source.title;
          item.append(link);
          references.append(item);
        }
        box.append(references);
      }
      this.conversation.append(box);
      this.scrollAnswerToStart(box);
    }
  }

  customElements.define("reality-journey-chat", RealityJourneyChat);
  document.body.append(document.createElement("reality-journey-chat"));
})();
