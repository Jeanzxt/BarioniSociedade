"""Gera retratos WebP e a imagem institucional para compartilhamento.

Uso: .venv\\Scripts\\python.exe scripts/prepare_assets.py
Dependencias de desenvolvimento: Playwright para Python e Microsoft Edge.
Os JPEGs originais e o monograma SVG sao preservados. Nenhuma fonte externa e usada.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
STATE_PATH = ROOT / "scripts" / "assets-state.json"
WIDTHS = (360, 720)


def make_portraits(page, lawyers: list) -> None:
    """Redimensiona proporcionalmente, sem recorte, retoque ou alteracao de cores."""
    for lawyer in lawyers:
        original, stem = lawyer["foto"], lawyer["imagem_base"]
        source = ASSETS / original
        page.goto(source.as_uri())
        page.locator("img").evaluate("image => image.decode()")
        for width in WIDTHS:
            rendered = page.locator("img").evaluate(
                """(image, requestedWidth) => {
                    const canvas = document.createElement('canvas');
                    canvas.width = Math.min(requestedWidth, image.naturalWidth);
                    canvas.height = Math.round(canvas.width * image.naturalHeight / image.naturalWidth);
                    const context = canvas.getContext('2d', {alpha: false});
                    context.imageSmoothingEnabled = true;
                    context.imageSmoothingQuality = 'high';
                    context.drawImage(image, 0, 0, canvas.width, canvas.height);
                    return {
                        data: canvas.toDataURL('image/webp', 0.88),
                        width: canvas.width,
                        height: canvas.height
                    };
                }""",
                width,
            )
            if not rendered["data"].startswith("data:image/webp;base64,"):
                raise RuntimeError("O navegador nao conseguiu codificar imagens WebP.")
            target = ASSETS / f"{stem}-{width}.webp"
            target.write_bytes(base64.b64decode(rendered["data"].split(",", 1)[1]))
            print(f"{target.relative_to(ROOT)}: {rendered['width']}x{rendered['height']}, {target.stat().st_size:,} bytes")


def social_card_html(office: dict) -> str:
    title = office["nome_curto"]
    suffix = office["subtitulo"]
    location = f"{office['cidade']}, {office['estado_nome']}"
    foundation = office["ano_fundacao"]
    logo = (ASSETS / "brand-mark.svg").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{ background: #152831; color: #f8f6f1; font-family: 'Segoe UI', Arial, sans-serif; }}
.card {{ width: 1200px; height: 630px; position: relative; padding: 87px 94px 70px; }}
.frame {{ position: absolute; inset: 28px; border: 1px solid #c4a36b50; }}
.rule {{ width: 58px; height: 2px; margin-bottom: 32px; background: #c4a36b; }}
.eyebrow {{ color: #c4a36b; font-size: 18px; letter-spacing: 4px; text-transform: uppercase; }}
h1 {{ position: relative; margin: 27px 0 39px; font: 400 76px/1.12 Georgia, 'Times New Roman', serif; letter-spacing: -2.8px; }}
.slogan {{ margin: 0; font: 400 32px/1.4 Georgia, 'Times New Roman', serif; }}
.slogan em {{ color: #d7bd92; }}
.location {{ position: absolute; bottom: 74px; left: 96px; margin: 0; font-size: 20px; color: #dce0de; letter-spacing: 0.3px; }}
.location .dot {{ color: #c4a36b; padding: 0 12px; }}
.mark {{ position: absolute; width: 244px; height: 244px; right: 77px; top: 179px; }}
.mark svg {{ display: block; width: 100%; height: 100%; }}
</style></head>
<body><main class="card">
<div class="frame"></div>
<div class="rule"></div>
<div class="eyebrow">{html.escape(suffix)}</div>
<h1>{html.escape(title)}</h1>
<p class="slogan">Clareza para decidir.<br><em>Segurança para seguir.</em></p>
<p class="location">{html.escape(location)}<span class="dot">·</span>Desde {html.escape(str(foundation))}</p>
<div class="mark">{logo}</div>
</main></body></html>"""


def make_social_card(page, office: dict) -> None:
    # Um documento de imagem file:// nao tem o ciclo de carga de uma pagina HTML.
    page.goto("about:blank")
    page.set_viewport_size({"width": 1200, "height": 630})
    page.set_content(social_card_html(office), wait_until="load")
    page.evaluate("document.fonts.ready")
    target = ASSETS / "social-card.png"
    page.screenshot(path=str(target), full_page=False, animations="disabled")
    print(f"{target.relative_to(ROOT)}: 1200x630, {target.stat().st_size:,} bytes")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def current(entry: dict, source_hash: str, outputs: list[Path]) -> bool:
    if not isinstance(entry, dict) or entry.get("source_hash") != source_hash:
        return False
    recorded = entry.get("outputs", {})
    return all(path.is_file() and recorded.get(path.name) == file_hash(path) for path in outputs)


def state_entry(source_hash: str, outputs: list[Path]) -> dict:
    return {"source_hash": source_hash, "outputs": {path.name: file_hash(path) for path in outputs}}


def ensure_assets(*, force=False, portraits=True, social=True) -> bool:
    """Atualiza apenas assets desatualizados; cache valido dispensa Playwright.

    Retorna True se algum arquivo foi gerado. O estado interno guarda hashes dos
    insumos e resultados: dados sem efeito visual nao invalidam as imagens.
    """
    data = json.loads((ROOT / "dados.json").read_text(encoding="utf-8-sig"))
    office = data["informacoes_escritorio"]
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    script_hash = file_hash(Path(__file__))
    pending = []
    for lawyer in data["advogados"] if portraits else []:
        source_name, stem = lawyer["foto"], lawyer["imagem_base"]
        if Path(source_name).name != source_name or Path(stem).name != stem:
            raise ValueError("Os nomes de imagens devem ser arquivos diretamente em assets/.")
        outputs = [ASSETS / f"{stem}-{width}.webp" for width in WIDTHS]
        source_hash = fingerprint({"script": script_hash, "foto": source_name,
                                   "imagem_base": stem, "original": file_hash(ASSETS / source_name)})
        key = "portrait:" + stem
        if force or not current(state.get(key, {}), source_hash, outputs):
            pending.append((key, source_hash, outputs, lawyer))
    social_hash = ""
    social_outputs = [ASSETS / "social-card.png"]
    social_pending = False
    if social:
        social_hash = fingerprint({
            "script": script_hash,
            "logo": file_hash(ASSETS / "brand-mark.svg"),
            "office": {key: office[key] for key in
                       ("nome_curto", "subtitulo", "cidade", "estado_nome", "ano_fundacao")},
        })
        social_pending = force or not current(state.get("social", {}), social_hash, social_outputs)
    if not pending and not social_pending:
        return False

    # Importacao deliberadamente tardia: builds comuns usam apenas a stdlib.
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
            if pending:
                make_portraits(page, [lawyer for _, _, _, lawyer in pending])
            if social_pending:
                make_social_card(page, office)
        finally:
            browser.close()
    for key, source_hash, outputs, _ in pending:
        state[key] = state_entry(source_hash, outputs)
    if social_pending:
        state["social"] = state_entry(social_hash, social_outputs)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--portraits-only", action="store_true", help="Gerar somente variantes WebP.")
    mode.add_argument("--social-only", action="store_true", help="Atualizar somente a imagem institucional.")
    parser.add_argument("--force", action="store_true", help="Regenerar mesmo quando o cache estiver atualizado.")
    args = parser.parse_args()
    changed = ensure_assets(force=args.force, portraits=not args.social_only, social=not args.portraits_only)
    if not changed:
        print("Assets atualizados; nenhuma imagem precisou ser regenerada.")


if __name__ == "__main__":
    main()
