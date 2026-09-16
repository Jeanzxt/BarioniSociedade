#!/usr/bin/env python3
"""Servidor de desenvolvimento local do site Willian Barioni."""

import argparse
import http.server
import sys
import webbrowser
from functools import partial
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts.site_policy import PUBLIC_FILES, SECURITY_HEADERS, REDIRECTS

DIRECTORY = Path(__file__).resolve().parent
PUBLIC_PATHS = frozenset(PUBLIC_FILES)


class SiteRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serve arquivos públicos, sem listagem de diretórios ou cache."""

    server_version = "BarioniLocal"
    sys_version = ""
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
        ".xml": "application/xml; charset=utf-8",
    }

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        try:
            content = (DIRECTORY / "404.html").read_bytes()
        except OSError:
            return super().send_error(code, message, explain)
        self.send_response(404, "Not Found")
        self.send_header("Connection", "close")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        for name, value in SECURITY_HEADERS.items():
            # O servidor local usa HTTP; HSTS pertence à hospedagem com HTTPS.
            if name.lower() != "strict-transport-security":
                self.send_header(name, value)
        super().end_headers()

    def send_head(self):
        requested_parts = unquote(urlsplit(self.path).path).replace("\\", "/").split("/")
        if any(
            part.startswith(".") or ":" in part
            for part in requested_parts
        ):
            self.send_error(404, "Arquivo não encontrado")
            return None

        try:
            target = Path(self.translate_path(self.path)).resolve()
            if target.is_dir():
                target = (target / "index.html").resolve()
            relative = target.relative_to(DIRECTORY)
        except (OSError, ValueError):
            self.send_error(404, "Arquivo não encontrado")
            return None

        if relative.as_posix() not in PUBLIC_PATHS:
            self.send_error(404, "Arquivo não encontrado")
            return None

        if relative.as_posix() in REDIRECTS:
            location = '/' + REDIRECTS[relative.as_posix()]
            query = urlsplit(self.path).query
            if query:
                location += '?' + query
            self.send_response(301)
            self.send_header('Location', location)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None

        # Atualizações locais devem aparecer até quando o navegador envia esta condição.
        if "If-Modified-Since" in self.headers:
            del self.headers["If-Modified-Since"]
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404, "Arquivo não encontrado")
        return None


def valid_port(value):
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Informe uma porta entre 1 e 65535.") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Informe uma porta entre 1 e 65535.")
    return port


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=valid_port, default=8000, help="Porta local (padrão: 8000).")
    parser.add_argument("--no-browser", action="store_true", help="Iniciar sem abrir o navegador.")
    args = parser.parse_args()
    handler = partial(SiteRequestHandler, directory=str(DIRECTORY))

    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as exc:
        print(f"Não foi possível iniciar o servidor na porta {args.port}: {exc}", file=sys.stderr)
        print("Se a porta estiver ocupada, use --port 8001 ou encerre o servidor anterior.", file=sys.stderr)
        return 1

    with server:
        url = f"http://localhost:{args.port}"
        print(f"Site disponível em {url}", flush=True)
        print("Acesso restrito a este computador. Pressione Ctrl+C para encerrar.", flush=True)
        if not args.no_browser:
            try:
                if not webbrowser.open(url, new=2):
                    print("Abra o endereço acima no navegador.", flush=True)
            except webbrowser.Error:
                print("Abra o endereço acima no navegador.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
