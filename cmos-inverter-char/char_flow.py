import os
import re
import shutil
import subprocess
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Locate ngspice_con on Windows or ngspice on Linux/PATH
NGSPICE_BIN = shutil.which("ngspice_con") or shutil.which("ngspice") or r"E:\programs\Spice64\bin\ngspice_con.exe"

SLEWS_PS = [10, 25, 50, 100]
LOADS_FF = [2, 5, 10, 20]


def run_sweep():
    with open("inverter.sp", "r") as f:
        base_netlist = f.read()

    tphl_matrix = np.zeros((len(SLEWS_PS), len(LOADS_FF)))
    tplh_matrix = np.zeros((len(SLEWS_PS), len(LOADS_FF)))

    for i, slew in enumerate(SLEWS_PS):
        for j, load in enumerate(LOADS_FF):
            netlist = re.sub(r"\.param SLEW_IN = .*", f".param SLEW_IN = {slew}p", base_netlist)
            netlist = re.sub(r"\.param C_LOAD  = .*", f".param C_LOAD  = {load}f", netlist)

            with open("temp_run.sp", "w") as f:
                f.write(netlist)

            proc = subprocess.run([NGSPICE_BIN, "-b", "temp_run.sp"], capture_output=True, text=True)
            log = proc.stdout + proc.stderr

            m_hl = re.search(r"tphl\s*=\s*([0-9.eE+-]+)", log, re.IGNORECASE)
            m_lh = re.search(r"tplh\s*=\s*([0-9.eE+-]+)", log, re.IGNORECASE)

            if m_hl and m_lh:
                tphl_matrix[i, j] = float(m_hl.group(1)) * 1e12
                tplh_matrix[i, j] = float(m_lh.group(1)) * 1e12
            else:
                print(f"[WARN] Measurement missed at slew={slew}ps, load={load}fF")

    if os.path.exists("temp_run.sp"):
        os.remove("temp_run.sp")

    return tphl_matrix, tplh_matrix


def write_liberty(tphl_matrix, filename="inv_x1.lib"):
    slew_idx = ", ".join(map(str, SLEWS_PS))
    load_idx = ", ".join(map(str, LOADS_FF))

    lines = [
        "/* Liberty (.lib) NLDM Timing Model - INV_X1 */",
        "cell (INV_X1) {",
        "  area : 1.0;",
        "  pin (Y) {",
        "    direction : output;",
        '    function : "!A";',
        "    timing () {",
        '      related_pin : "A";',
        "      cell_fall (delay_template_4x4) {",
        f'        index_1 ("{slew_idx}");',
        f'        index_2 ("{load_idx}");',
        "        values ( \\",
    ]

    for idx, row in enumerate(tphl_matrix):
        vals = ", ".join(f"{v:.2f}" for v in row)
        suffix = " \\" if idx < len(tphl_matrix) - 1 else " );"
        lines.append(f'          "{vals}"{suffix}')

    lines.extend(["      }", "    }", "  }", "}"])

    with open(filename, "w") as f:
        f.write("\n".join(lines) + "\n")


def plot_delay(tphl_matrix, filename="delay_vs_load.png"):
    plt.figure(figsize=(7, 4.5))
    for i, slew in enumerate(SLEWS_PS):
        plt.plot(LOADS_FF, tphl_matrix[i], marker="o", label=f"Input Slew = {slew} ps")

    plt.title("CMOS Inverter Propagation Delay (tpHL) vs. Load Capacitance")
    plt.xlabel("Output Load Capacitance (fF)")
    plt.ylabel("Propagation Delay tpHL (ps)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=200)


if __name__ == "__main__":
    print("Running SPICE characterization sweeps...")
    tphl, tplh = run_sweep()
    write_liberty(tphl)
    plot_delay(tphl)
    print("Done. Generated inv_x1.lib and delay_vs_load.png")