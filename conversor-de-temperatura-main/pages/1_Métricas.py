import streamlit as st
import subprocess, sys, re, json, os, ast, pathlib, xml.etree.ElementTree as ET
from datetime import datetime

st.set_page_config(page_title="Métricas", page_icon="📊", layout="centered")
st.title("Métricas")
st.write("Use um dos botões abaixo:")

def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def count_loc(path: pathlib.Path) -> int:
    loc = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        loc += 1
    return loc

def count_funcs(path: pathlib.Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))

def discover_python_files() -> list[pathlib.Path]:
    root = pathlib.Path(".")
    files = []
    files += sorted(root.glob("*.py"))
    files += sorted((root / "pages").glob("*.py"))
    files = [f for f in files if "__pycache__" not in str(f)]
    return files

st.divider()

# =========================
# Botão 1 — PYTEST REPORT
# =========================
if st.button("Rodar testes (pytest)", type="secondary", use_container_width=True):
    # roda pytest com XML JUnit (para extrair métricas)
    xml_path = "pytest_report.xml"
    code, out = run([sys.executable, "-m", "pytest", "-q", "-rA", f"--junitxml={xml_path}"])

    # resumo “humano”
    m = re.search(r"(\d+)\s+passed.*?in\s+([\d\.]+)s", out)
    passed = int(m.group(1)) if m else None
    time_s = float(m.group(2)) if m else None

    st.subheader("Saída dos testes")
    if code == 0:
        if passed is not None and time_s is not None:
            st.success(f"Testes passaram: {passed} • Tempo: {time_s:.3f}s")
        else:
            st.success(" Testes passaram.")
        with st.expander("Ver detalhes do pytest"):
            st.code(out or "(sem saída)", language=None)
    else:
        st.error("Alguns testes falharam. Veja os detalhes abaixo.")
        st.code(out or "(sem saída)", language=None)

    # --- constrói relatório a partir do JUnit XML ---
    summary = {"tests": 0, "errors": 0, "failures": 0, "skipped": 0, "time": 0.0}
    rows = []  # cada teste: arquivo.classe::teste, status, tempo

    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            # pytest pode gerar <testsuite> (raiz) ou <testsuites> com vários filhos
            suites = []
            if root.tag == "testsuites":
                suites = list(root)
            elif root.tag == "testsuite":
                suites = [root]

            for ts in suites:
                summary["tests"] += int(ts.attrib.get("tests", 0))
                summary["errors"] += int(ts.attrib.get("errors", 0))
                summary["failures"] += int(ts.attrib.get("failures", 0))
                summary["skipped"] += int(ts.attrib.get("skipped", 0) or 0)
                summary["time"] += float(ts.attrib.get("time", 0.0) or 0.0)

                for tc in ts.findall("testcase"):
                    classname = tc.attrib.get("classname", "")
                    name = tc.attrib.get("name", "")
                    t = float(tc.attrib.get("time", 0.0) or 0.0)

                    status = "passed"
                    if tc.find("failure") is not None:
                        status = "failed"
                    elif tc.find("error") is not None:
                        status = "error"
                    elif tc.find("skipped") is not None:
                        status = "skipped"

                    id_display = f"{classname}::{name}" if classname else name
                    rows.append({"Teste": id_display, "Status": status, "Tempo (s)": round(t, 6)})

            # ordena por tempo desc
            rows.sort(key=lambda r: r["Tempo (s)"], reverse=True)

            # mostra tabela (compacta: top 50 se for muito grande)
            st.subheader("Relatório do pytest (por teste)")
            if len(rows) > 0:
                max_rows = 50
                show = rows[:max_rows]
                st.table(show)
                if len(rows) > max_rows:
                    st.caption(f"Mostrando {max_rows} mais lentos de {len(rows)} testes.")
            else:
                st.caption("Sem casos de teste no XML.")

            # gera Markdown
            dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
            md_lines = [
                "# 🧪 Relatório de Testes (pytest)",
                "",
                f"**Data (UTC):** {dt}",
                "",
                "## ✅ Resumo",
                f"- Total de testes: **{summary['tests']}**",
                f"- Passaram: **{summary['tests'] - summary['errors'] - summary['failures'] - summary['skipped']}**",
                f"- Falhas: **{summary['failures']}**",
                f"- Erros: **{summary['errors']}**",
                f"- Skipped: **{summary['skipped']}**",
                f"- Tempo total: **{summary['time']:.3f}s**",
                "",
                "## Detalhes por teste (top 50 por tempo)",
                "",
                "| Teste | Status | Tempo (s) |",
                "|---|---|---:|",
            ]
            for r in rows[:50]:
                md_lines.append(f"| `{r['Teste']}` | {r['Status']} | {r['Tempo (s)']:.6f} |")

            md_pytest = "\n".join(md_lines)
            with open("pytest_report.md", "w", encoding="utf-8") as f:
                f.write(md_pytest)

            st.success("Relatório Markdown gerado: `pytest_report.md`")
            with st.expander("Visualizar pytest_report.md"):
                st.markdown(md_pytest)

            st.download_button(
                "Baixar pytest_report.md",
                data=md_pytest.encode("utf-8"),
                file_name="pytest_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Falha ao processar o XML do pytest: {e}")
    else:
        st.info("pytest_report.xml não foi encontrado. Rode novamente ou verifique permissões.")

st.divider()

# ===================================
# Botão 2 — COVERAGE + MÉTRICAS .MD
# ===================================
if st.button("Rodar testes(coverage)", type="primary", use_container_width=True):
    run([sys.executable, "-m", "coverage", "erase"])
    code, out = run([sys.executable, "-m", "coverage", "run", "-m", "pytest", "-q"])

    m = re.search(r"(\d+)\s+passed.*?in\s+([\d\.]+)s", out)
    passed = int(m.group(1)) if m else None
    time_s = float(m.group(2)) if m else None

    st.subheader("Saída dos testes")
    if code == 0:
        if passed is not None and time_s is not None:
            st.success(f"Testes passaram: {passed} • Tempo: {time_s:.3f}s")
        else:
            st.success("✅ Testes passaram.")
        with st.expander("Ver detalhes do pytest"):
            st.code(out or "(sem saída)", language=None)
    else:
        st.error("Alguns testes falharam. Veja os detalhes abaixo.")
        st.code(out or "(sem saída)", language=None)

    _, cov_text = run([sys.executable, "-m", "coverage", "report", "-m"])
    run([sys.executable, "-m", "coverage", "json", "-o", "coverage.json"])

    percent = 0.0
    m_cov = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+(\d+)%", cov_text)
    if m_cov:
        percent = float(m_cov.group(1))
    elif os.path.exists("coverage.json"):
        data_tot = json.load(open("coverage.json", "r", encoding="utf-8"))
        percent = float(data_tot.get("totals", {}).get("percent_covered", 0.0))

    st.subheader("Cobertura")
    st.markdown(f"**Cobertura total (linhas): {percent:.1f}%**")
    with st.expander("Detalhes (coverage report)"):
        st.code(cov_text.strip(), language=None)

    cov_by_file: dict[str, float] = {}
    if os.path.exists("coverage.json"):
        data_json = json.load(open("coverage.json", "r", encoding="utf-8"))
        for abs_path, info in data_json.get("files", {}).items():
            rel = pathlib.Path(abs_path)
            try:
                rel = rel.relative_to(pathlib.Path.cwd())
            except Exception:
                pass
            cov_by_file[str(rel).replace("\\", "/")] = float(info.get("summary", {}).get("percent_covered", 0.0))

    rows = []
    for p in discover_python_files():
        key1 = str(p).replace("\\", "/")
        key2 = str(p.resolve()).replace("\\", "/")
        cov = cov_by_file.get(key1, cov_by_file.get(key2, 0.0))
        rows.append({
            "Arquivo": str(p),
            "Linhas (LOC)": count_loc(p),
            "Funções (def)": count_funcs(p),
            "Cobertura (%)": round(cov, 1),
        })

    if rows:
        rows = sorted(rows, key=lambda r: r["Arquivo"])
        st.subheader("Relatório de métricas por arquivo")
        st.table(rows)

        dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        md_lines = [
            "# Relatório de Métricas — Conversor de Temperatura",
            "",
            f"**Data (UTC):** {dt}",
            "",
            "## ✅ Testes",
            f"- Resultado: {'**PASSOU** ✅' if code == 0 else '**FALHOU** ❌'}",
        ]
        if passed is not None and time_s is not None:
            md_lines.append(f"- Testes executados (pass): **{passed}**")
            md_lines.append(f"- Tempo total: **{time_s:.3f}s**")
        md_lines += [
            "",
            "## 🧮 Cobertura",
            f"- Cobertura total (linhas): **{percent:.1f}%**",
            "",
            "## 📁 Métricas por arquivo",
            "",
            "| Arquivo | Linhas (LOC) | Funções (def) | Cobertura (%) |",
            "|---|---:|---:|---:|",
        ]
        for r in rows:
            md_lines.append(f"| {r['Arquivo']} | {r['Linhas (LOC)']} | {r['Funções (def)']} | {r['Cobertura (%)']:.1f}% |")

        md = "\n".join(md_lines)
        with open("metrics_report.md", "w", encoding="utf-8") as f:
            f.write(md)

        st.success("Relatório Markdown gerado: `metrics_report.md`")
        with st.expander("Visualizar metrics_report.md"):
            st.markdown(md)

        st.download_button(
            "Baixar metrics_report.md",
            data=md.encode("utf-8"),
            file_name="metrics_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    if os.path.exists("coverage.json"):
        st.download_button(
            "Baixar coverage.json",
            data=open("coverage.json", "rb"),
            file_name="coverage.json",
            mime="application/json",
            use_container_width=True,
        )
