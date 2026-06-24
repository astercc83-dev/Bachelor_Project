import { useState, useEffect, useRef } from "react";

// ─── Study content ──────────────────────────────────────────────────────────
const DAYS = [
  {
    id: "d1",
    node: "ADC",
    title: "ADC — how the real world becomes numbers",
    mission:
      "What physically happens between the voltage on the wire and the number 0.8766 in Python?",
    readings: [
      {
        label: "NI Specs Explained → ADC Resolution, Sample Rate, Range",
        url: "https://www.ni.com/en/support/documentation/supplemental/16/specifications-explained--ni-multifunction-i-o--mio--daq.html",
      },
    ],
    ideas: [
      "ADC samples the voltage at the sample-clock rate and outputs a binary code.",
      "16-bit = 65,536 steps. On ±10 V → step ≈ 0.305 mV. Smaller range = finer steps.",
      "Your card: 20 kS/s … 50 MS/s. The -200077 error below 20 kS/s is a hardware clock limit.",
      "Find out: is YOUR card multiplexed (one ADC shared) or simultaneous (ADC per channel)?",
    ],
    selfChecks: [
      {
        q: "If my card is 16-bit on ±1 V range, what is the smallest voltage change it can see?",
        a: "2 V range ÷ 65,536 steps ≈ 30.5 µV per step.",
      },
      {
        q: "Why does a smaller input range give better resolution?",
        a: "Same 65,536 steps spread over fewer volts → each step is smaller → finer detail.",
      },
    ],
  },
  {
    id: "d2",
    node: "FIFO",
    title: "Onboard FIFO — the card's tiny shock absorber",
    mission:
      "Why does the card need its own memory, and why is 12,287 samples enough?",
    readings: [
      {
        label: "NI Specs Explained → FIFO Size (Analog) — THE key section",
        url: "https://www.ni.com/en/support/documentation/supplemental/16/specifications-explained--ni-multifunction-i-o--mio--daq.html",
      },
      { label: "Re-read your own Buffer_Overflow_Report.md §1–2", url: null },
    ],
    ideas: [
      "FIFO = hardware queue ON the card, right after the ADC. A shock absorber, not a storage tank.",
      "Shared across all 8 channels of the card — divide by 8 for multi-channel!",
      "NI's own PXIe-6363 has only 2,047 samples. Your 12,287 is ~6× larger.",
      "At 50 MS/s: 12,287 ÷ 50e6 ≈ 0.25 ms headroom — fine, DMA drains it every few µs.",
    ],
    selfChecks: [
      {
        q: "FIFO headroom at 1 MS/s? At 50 MS/s?",
        a: "12,287/1e6 ≈ 12.3 ms at 1 MS/s. 12,287/50e6 ≈ 0.25 ms at 50 MS/s.",
      },
      {
        q: "Who empties the FIFO — Python, the driver, or hardware?",
        a: "DMA hardware. No CPU, no Python involved at all.",
      },
    ],
  },
  {
    id: "d3",
    node: "FPGA",
    title: "FPGA — the card's brain that never sleeps",
    mission: "What is the FPGA and what does it do on a DAQ card?",
    readings: [
      { label: 'Search ni.com for "FPGA Fundamentals" (intro page)', url: null },
    ],
    ideas: [
      "FPGA = chip whose logic is configured as the DAQ engine by NI.",
      "It: locks the sample clock, triggers the ADC, fills the FIFO, raises DMA requests, handles triggers.",
      "All in parallel, in hardware, zero jitter — independent of Windows AND Python.",
      "Your proof: you slept 0.5 s and samples kept arriving. The FPGA never stopped.",
    ],
    selfChecks: [
      {
        q: "Why can't Windows timing jitter affect sample spacing?",
        a: "The FPGA's hardware clock drives the ADC directly — the OS is not in the loop.",
      },
      {
        q: "What happens when the FIFO is full and DMA hasn't drained it?",
        a: "FIFO overrun — the hardware-level overflow, different from -200279.",
      },
    ],
  },
  {
    id: "d4",
    node: "DMA",
    title: "DMA — moving 400 MB/s with zero CPU",
    mission:
      "How do samples travel from the card's FIFO into PC RAM with no CPU work?",
    readings: [
      {
        label: "NI KB: What is Scatter-Gather DMA?",
        url: "https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z0000019NMqSAM",
      },
      {
        label: "NI Specs Explained → Data Transfer Mechanisms",
        url: "https://www.ni.com/en/support/documentation/supplemental/16/specifications-explained--ni-multifunction-i-o--mio--daq.html",
      },
    ],
    ideas: [
      "DMA = dedicated transfer engine writing straight into reserved RAM over the PXIe backplane.",
      "CPU sets it up once — afterwards data flows by itself. This is why 50 MS/s is possible.",
      "Alternative = Programmed I/O (CPU copies every sample) → far too slow.",
      "Scatter-gather: RAM doesn't need one physical block; DMA follows a chunk list.",
    ],
    selfChecks: [
      {
        q: "50 MS/s × 8 bytes/sample = how many MB/s?",
        a: "400 MB/s — why USB DAQ can't do this, but PXIe can.",
      },
      {
        q: "What happens to the FIFO if DMA stops for 1 ms at 50 MS/s?",
        a: "50,000 samples arrive but FIFO holds 12,287 → hardware overrun in ~0.25 ms.",
      },
    ],
  },
  {
    id: "d5",
    node: "HOST BUF",
    title: "Host Buffer — where error -200279 lives",
    mission:
      "Where exactly does -200279 happen, and how do I control that memory?",
    readings: [
      {
        label: "nidaqmx Python docs → InStream (input_buf_size, avail_samp_per_chan)",
        url: "https://nidaqmx-python.readthedocs.io/",
      },
      {
        label: "NI-DAQmx properties reference",
        url: "https://www.ni.com/docs/en-US/bundle/ni-daqmx-properties/page/daqmxprop/daqmxchannel.html",
      },
    ],
    ideas: [
      "Circular buffer in PC RAM, allocated by the driver for CONTINUOUS timing.",
      "DMA writes in, task.read() takes out. Write pointer catches read pointer → -200279.",
      "You can READ its size (1,000,000 on your system) and you can SET it bigger.",
      "avail_samp_per_chan = live fill-level meter = your early-warning system.",
    ],
    selfChecks: [
      {
        q: "At 10 MS/s, how long can Python sleep before -200279?",
        a: "1e6 ÷ 10e6 = 100 ms. You slept 500 ms → crash. Your numbers match the theory!",
      },
      {
        q: "Is -200279 a hardware error or a software error?",
        a: "Software/driver level — the hardware (FIFO, DMA) was perfectly fine.",
      },
    ],
  },
  {
    id: "d6",
    node: "DATASHEET",
    title: "Your exact card — the official numbers",
    mission:
      "Get product_type from the PXI, find the official datasheet, extract the spec table.",
    readings: [
      {
        label: "NI specification manuals search (after you have product_type)",
        url: "https://www.ni.com/en-us/search.html?pg=1&ps=10&sn=catnav%3Asup.man%2Cn14%3Aspecifications%2Cn8%3A3478",
      },
    ],
    ideas: [
      "On the PXI run: for d in System.local().devices: print(d.name, d.product_type)",
      "Extract: ADC bits, multiplexed vs simultaneous, max rates, FIFO size, input ranges, transfer mechanisms.",
      "FIFO in the datasheet should match your measured 12,287!",
      "This table + the PDF citation goes straight into the report's hardware chapter.",
    ],
    selfChecks: [
      {
        q: "Why does Dr. Amayreh want the official datasheet and not just your measured values?",
        a: "Measured values prove your system works; the datasheet is the citable scientific source. Report needs both.",
      },
    ],
  },
  {
    id: "d7",
    node: "FULL CHAIN",
    title: "Tell the whole story from memory",
    mission:
      "No reading. Close everything and narrate the full chain: wire → ADC → FIFO → DMA → host buffer → task.read() → -200279 → your architecture fix.",
    readings: [],
    ideas: [
      "A voltage appears on the wire. The FPGA's clock triggers the ADC every 1/rate seconds.",
      "The ADC code goes into the 12,287-sample FIFO; DMA drains it into the 1M-sample circular host buffer.",
      "task.read() consumes from the host buffer. Too slow → wrap-around → -200279 (you demonstrated it).",
      "Your fix: Reader process only reads & copies to shared memory; processing/saving live on other cores.",
    ],
    selfChecks: [
      {
        q: "Can you say the full paragraph fluently, out loud, without notes?",
        a: "If yes — you are done. That paragraph IS the project. Go shock Dr. Amayreh.",
      },
    ],
  },
];

const TASKS = [
  { key: "read", label: "Read the docs" },
  { key: "notes", label: "Write 5 lines in your own words" },
  { key: "check", label: "Answer self-checks out loud" },
];

const LEVELS = [
  "SIGNAL ROOKIE",
  "ADC APPRENTICE",
  "FIFO FIGHTER",
  "FPGA WHISPERER",
  "DMA DRIVER",
  "BUFFER BOSS",
  "DATASHEET DETECTIVE",
  "HARDWARE HERO",
];

const XP_PER_TASK = 25;
const DAY_BONUS = 25;
const MAX_XP = DAYS.length * (TASKS.length * XP_PER_TASK + DAY_BONUS); // 700

const STORAGE_KEY = "hw-study-progress-v1";

// ─── Component ──────────────────────────────────────────────────────────────
export default function HardwareStudyTracker() {
  const [checks, setChecks] = useState({});
  const [openDay, setOpenDay] = useState("d1");
  const [revealed, setRevealed] = useState({});
  const [loaded, setLoaded] = useState(false);
  const [saveState, setSaveState] = useState("idle"); // idle | saving | saved | error
  const saveTimer = useRef(null);

  // Load persisted progress
  useEffect(() => {
    (async () => {
      try {
        const result = await window.storage.get(STORAGE_KEY);
        if (result && result.value) {
          const parsed = JSON.parse(result.value);
          if (parsed.checks) setChecks(parsed.checks);
          if (parsed.openDay) setOpenDay(parsed.openDay);
        }
      } catch (e) {
        // first run — no saved progress yet
      }
      setLoaded(true);
    })();
  }, []);

  // Persist on change (debounced lightly)
  useEffect(() => {
    if (!loaded) return;
    setSaveState("saving");
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      try {
        await window.storage.set(
          STORAGE_KEY,
          JSON.stringify({ checks, openDay })
        );
        setSaveState("saved");
      } catch (e) {
        setSaveState("error");
      }
    }, 400);
    return () => saveTimer.current && clearTimeout(saveTimer.current);
  }, [checks, openDay, loaded]);

  const dayChecks = (id) => checks[id] || {};
  const dayDone = (id) => TASKS.every((t) => dayChecks(id)[t.key]);
  const tasksDone = (id) => TASKS.filter((t) => dayChecks(id)[t.key]).length;

  const xp = DAYS.reduce(
    (sum, d) =>
      sum + tasksDone(d.id) * XP_PER_TASK + (dayDone(d.id) ? DAY_BONUS : 0),
    0
  );
  const completedDays = DAYS.filter((d) => dayDone(d.id)).length;
  const level = Math.min(completedDays, LEVELS.length - 1);
  const fillPct = Math.round((xp / MAX_XP) * 100);
  const currentDayIdx = DAYS.findIndex((d) => !dayDone(d.id));

  const toggle = (dayId, key) =>
    setChecks((prev) => ({
      ...prev,
      [dayId]: { ...(prev[dayId] || {}), [key]: !(prev[dayId] || {})[key] },
    }));

  const resetAll = async () => {
    setChecks({});
    setRevealed({});
    setOpenDay("d1");
    try {
      await window.storage.delete(STORAGE_KEY);
    } catch (e) {}
  };

  const graticule = {
    backgroundImage:
      "linear-gradient(rgba(74,222,128,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(74,222,128,0.05) 1px, transparent 1px)",
    backgroundSize: "32px 32px",
  };

  return (
    <div
      className="min-h-screen bg-slate-950 text-slate-300 font-mono"
      style={graticule}
    >
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* ── Header / mission status ── */}
        <div className="border border-slate-700 bg-slate-900/80 rounded-lg p-5 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="text-xs text-green-400/70 tracking-widest">
                PXI BACHELOR PROJECT // HARDWARE DEEP-DIVE
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-100 mt-1">
                7-Day Mission: Understand the Machine
              </h1>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-500">OPERATOR LEVEL</div>
              <div
                className={`text-sm font-bold ${
                  level === LEVELS.length - 1
                    ? "text-amber-300"
                    : "text-green-400"
                }`}
              >
                {LEVELS[level]}
              </div>
            </div>
          </div>

          {/* Buffer-style XP bar */}
          <div className="mt-5">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">
                KNOWLEDGE BUFFER FILL —{" "}
                <span className="text-green-400">{xp}</span> / {MAX_XP} XP
              </span>
              <span
                className={fillPct === 100 ? "text-amber-300" : "text-slate-400"}
              >
                {fillPct}%
              </span>
            </div>
            <div
              className="h-4 bg-slate-800 rounded border border-slate-700 overflow-hidden"
              role="progressbar"
              aria-valuenow={fillPct}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className={`h-full transition-all duration-700 ${
                  fillPct === 100 ? "bg-amber-400" : "bg-green-500"
                }`}
                style={{ width: `${fillPct}%` }}
              />
            </div>
            <div className="text-xs text-slate-600 mt-1">
              Unlike the real host buffer — this one you WANT at 100%. No
              -200279 here.
            </div>
          </div>
        </div>

        {/* ── Signal chain visualization ── */}
        <div className="border border-slate-700 bg-slate-900/80 rounded-lg p-5 mb-6 overflow-x-auto">
          <div className="text-xs text-slate-500 mb-3 tracking-widest">
            SIGNAL CHAIN — lights up as you master each stage
          </div>
          <div className="flex items-center min-w-max">
            {DAYS.map((d, i) => {
              const done = dayDone(d.id);
              const isCurrent = i === currentDayIdx;
              return (
                <div key={d.id} className="flex items-center">
                  <button
                    onClick={() => setOpenDay(d.id)}
                    className={`flex flex-col items-center group focus-visible:outline focus-visible:outline-2 focus-visible:outline-green-400 rounded p-1`}
                    aria-label={`Open day ${i + 1}: ${d.node}`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                        done
                          ? "border-green-400 bg-green-500/20 text-green-300 shadow-[0_0_12px_rgba(74,222,128,0.5)]"
                          : isCurrent
                          ? "border-amber-400 text-amber-300 animate-pulse"
                          : "border-slate-700 text-slate-600"
                      }`}
                    >
                      {done ? "✓" : i + 1}
                    </div>
                    <div
                      className={`text-[10px] mt-1 tracking-wide ${
                        done
                          ? "text-green-400"
                          : isCurrent
                          ? "text-amber-300"
                          : "text-slate-600"
                      }`}
                    >
                      {d.node}
                    </div>
                  </button>
                  {i < DAYS.length - 1 && (
                    <div
                      className={`h-0.5 w-6 sm:w-9 transition-colors duration-500 ${
                        done ? "bg-green-400" : "bg-slate-700"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Day cards ── */}
        <div className="space-y-3">
          {DAYS.map((d, i) => {
            const open = openDay === d.id;
            const done = dayDone(d.id);
            const nTasks = tasksDone(d.id);
            return (
              <div
                key={d.id}
                className={`border rounded-lg overflow-hidden transition-colors ${
                  done
                    ? "border-green-700/60 bg-slate-900/60"
                    : open
                    ? "border-amber-500/50 bg-slate-900/80"
                    : "border-slate-800 bg-slate-900/50"
                }`}
              >
                <button
                  onClick={() => setOpenDay(open ? null : d.id)}
                  className="w-full text-left px-4 py-3 flex items-center justify-between gap-3 focus-visible:outline focus-visible:outline-2 focus-visible:outline-green-400"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className={`text-xs px-2 py-0.5 rounded border shrink-0 ${
                        done
                          ? "border-green-600 text-green-400"
                          : "border-slate-700 text-slate-500"
                      }`}
                    >
                      DAY {i + 1}
                    </span>
                    <span
                      className={`text-sm font-bold truncate ${
                        done ? "text-green-300" : "text-slate-200"
                      }`}
                    >
                      {d.title}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 shrink-0">
                    {done ? "+100 XP ✓" : `${nTasks}/${TASKS.length}`}
                  </span>
                </button>

                {open && (
                  <div className="px-4 pb-4 space-y-4 border-t border-slate-800 pt-4">
                    {/* Mission */}
                    <div className="bg-slate-950/70 border border-slate-800 rounded p-3">
                      <div className="text-[10px] text-amber-400/80 tracking-widest mb-1">
                        TODAY'S MISSION QUESTION
                      </div>
                      <div className="text-sm text-slate-200">{d.mission}</div>
                    </div>

                    {/* Readings */}
                    {d.readings.length > 0 && (
                      <div>
                        <div className="text-[10px] text-slate-500 tracking-widest mb-1">
                          READ
                        </div>
                        <ul className="space-y-1">
                          {d.readings.map((r, j) => (
                            <li key={j} className="text-sm">
                              {r.url ? (
                                <a
                                  href={r.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-green-400 hover:text-green-300 underline underline-offset-2 break-words"
                                >
                                  → {r.label}
                                </a>
                              ) : (
                                <span className="text-slate-300">
                                  → {r.label}
                                </span>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Core ideas */}
                    <div>
                      <div className="text-[10px] text-slate-500 tracking-widest mb-1">
                        CORE IDEAS TO OWN
                      </div>
                      <ul className="space-y-1.5">
                        {d.ideas.map((idea, j) => (
                          <li key={j} className="text-sm text-slate-300 flex gap-2">
                            <span className="text-green-500/70 shrink-0">▸</span>
                            <span>{idea}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Self checks */}
                    <div>
                      <div className="text-[10px] text-slate-500 tracking-widest mb-2">
                        SELF-CHECK — answer out loud, then reveal
                      </div>
                      <div className="space-y-2">
                        {d.selfChecks.map((sc, j) => {
                          const rKey = `${d.id}-${j}`;
                          const isRevealed = revealed[rKey];
                          return (
                            <div
                              key={j}
                              className="border border-slate-800 rounded p-3 bg-slate-950/50"
                            >
                              <div className="text-sm text-slate-200">
                                {sc.q}
                              </div>
                              {isRevealed ? (
                                <div className="text-sm text-green-300 mt-2 border-l-2 border-green-600 pl-2">
                                  {sc.a}
                                </div>
                              ) : (
                                <button
                                  onClick={() =>
                                    setRevealed((p) => ({
                                      ...p,
                                      [rKey]: true,
                                    }))
                                  }
                                  className="mt-2 text-xs px-2 py-1 border border-amber-600/60 text-amber-300 rounded hover:bg-amber-500/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-amber-400"
                                >
                                  REVEAL ANSWER
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Task checklist */}
                    <div>
                      <div className="text-[10px] text-slate-500 tracking-widest mb-2">
                        COMPLETE TO EARN XP (+{XP_PER_TASK} each, +{DAY_BONUS}{" "}
                        day bonus)
                      </div>
                      <div className="space-y-1.5">
                        {TASKS.map((t) => {
                          const on = !!dayChecks(d.id)[t.key];
                          return (
                            <button
                              key={t.key}
                              onClick={() => toggle(d.id, t.key)}
                              className={`w-full flex items-center gap-3 px-3 py-2 rounded border text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-green-400 ${
                                on
                                  ? "border-green-700 bg-green-500/10 text-green-300"
                                  : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
                              }`}
                              aria-pressed={on}
                            >
                              <span
                                className={`w-4 h-4 rounded-sm border flex items-center justify-center text-[10px] shrink-0 ${
                                  on
                                    ? "border-green-400 bg-green-500 text-slate-950"
                                    : "border-slate-600"
                                }`}
                              >
                                {on ? "✓" : ""}
                              </span>
                              {t.label}
                              <span className="ml-auto text-xs text-slate-500">
                                +{XP_PER_TASK} XP
                              </span>
                            </button>
                          );
                        })}
                      </div>
                      {done && (
                        <div className="mt-3 text-sm text-amber-300 border border-amber-600/40 bg-amber-500/10 rounded px-3 py-2">
                          ★ Day {i + 1} complete — stage "{d.node}" is now lit
                          on your signal chain. +{DAY_BONUS} XP bonus!
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Hero state ── */}
        {completedDays === DAYS.length && (
          <div className="mt-6 border-2 border-amber-400 bg-amber-500/10 rounded-lg p-5 text-center">
            <div className="text-2xl font-bold text-amber-300">
              ★ HARDWARE HERO ACHIEVED ★
            </div>
            <div className="text-sm text-slate-300 mt-2">
              You can now narrate the full chain — wire → ADC → FIFO → DMA →
              host buffer → -200279 → your fix — from memory. Go shock Dr.
              Amayreh.
            </div>
          </div>
        )}

        {/* ── Footer ── */}
        <div className="mt-6 flex items-center justify-between text-xs text-slate-600">
          <span>
            {saveState === "saving"
              ? "saving…"
              : saveState === "saved"
              ? "progress saved ✓ (persists across sessions)"
              : saveState === "error"
              ? "⚠ could not save progress"
              : ""}
          </span>
          <button
            onClick={resetAll}
            className="px-2 py-1 border border-slate-700 rounded text-slate-500 hover:text-red-400 hover:border-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-400"
          >
            RESET MISSION
          </button>
        </div>
      </div>
    </div>
  );
}
