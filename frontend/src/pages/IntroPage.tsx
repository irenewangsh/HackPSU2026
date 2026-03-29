import {
  motion,
  useScroll,
  useSpring,
  type Variants,
} from "framer-motion";
import { ArrowDown, Leaf, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

/** Opening page — Cormorant Garamond editorial type (FAQ reference), soft motion. */

const easeLux = [0.25, 0.1, 0.25, 1] as const;

const heroContainer: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.14, delayChildren: 0.06 },
  },
};

const fadeBlurUp: Variants = {
  hidden: { opacity: 0, y: 32, filter: "blur(10px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 1.05, ease: easeLux },
  },
};

const verseBlockParent: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.16 },
  },
};

const verseLine: Variants = {
  hidden: { opacity: 0, y: 22, filter: "blur(8px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.95, ease: easeLux },
  },
};

const labelClass =
  "font-sans text-[10px] font-semibold uppercase tracking-[0.42em] text-forest-600/78 md:text-[11px]";

function Verse({
  lines,
  attribution,
  className = "",
  tone = "light",
}: {
  lines: string[];
  attribution: string;
  className?: string;
  tone?: "light" | "dark";
}) {
  const sub =
    tone === "dark" ? "text-paper-3/80" : "text-forest-600/75";
  return (
    <motion.div
      className={`text-center ${className}`}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-10%" }}
      variants={verseBlockParent}
    >
      {lines.map((line, i) => (
        <motion.div
          key={i}
          variants={verseLine}
          className="experience-poetry block font-light leading-[1.42] tracking-[-0.015em] md:leading-[1.38]"
        >
          {line}
        </motion.div>
      ))}
      <motion.p
        variants={fadeBlurUp}
        className={`mt-12 font-sans text-[11px] font-medium uppercase tracking-[0.24em] ${sub}`}
      >
        {attribution}
      </motion.p>
    </motion.div>
  );
}

const faqItems = [
  {
    q: "What is SentinelOS?",
    a: "A supervisory layer between agents and the OS: policy, risk, hooks, and audit—not another chat UI.",
  },
  {
    q: "How does progressive trust work?",
    a: "Authority tightens or widens from events and memory decay, instead of a single static allow list.",
  },
  {
    q: "Where do file and exec hooks run?",
    a: "Inside your sandbox root, with native path checks when the C library is built; otherwise Python fallbacks.",
  },
];

export function IntroPage() {
  const topRef = useRef<HTMLDivElement>(null);
  const [headerSolid, setHeaderSolid] = useState(false);
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  useEffect(() => {
    const onScroll = () => setHeaderSolid(window.scrollY > 48);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const restart = () => topRef.current?.scrollIntoView({ behavior: "smooth" });

  return (
    <div ref={topRef} className="relative min-h-screen bg-[#f5f5f0] text-forest-900">
      <div className="relative z-10">
        <motion.div
          className="fixed left-0 right-0 top-0 z-40 h-[2px] origin-left bg-sage-600/70"
          style={{ scaleX }}
        />

        <header
          className={`fixed left-0 right-0 top-[2px] z-30 flex items-center justify-between px-6 py-5 transition-colors duration-500 md:px-14 ${
            headerSolid
              ? "bg-[#f5f5f0]/92 shadow-sm shadow-stone-300/25 backdrop-blur-md"
              : "bg-transparent"
          }`}
        >
          <div className="flex items-center gap-3">
            <Leaf className="h-5 w-5 text-sage-600" strokeWidth={1.5} />
            <span className="font-display text-[1.35rem] font-semibold tracking-tight text-ink md:text-2xl">
              Sentinel<span className="text-gradient">OS</span>
            </span>
          </div>
          <Link
            to="/dashboard"
            className="font-sans text-[11px] font-semibold uppercase tracking-[0.22em] text-forest-800 underline decoration-stone-400/55 underline-offset-[7px] transition hover:text-ink hover:decoration-sage-600"
          >
            Console
          </Link>
        </header>

        {/* Hero — centered, luxury serif */}
        <section className="relative flex min-h-[100dvh] flex-col justify-center overflow-hidden pb-28 pt-28 md:pb-36 md:pt-32">
          <div
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_70%_at_50%_0%,rgba(220,238,224,0.38),transparent_58%),radial-gradient(ellipse_55%_45%_at_50%_100%,rgba(243,228,220,0.32),transparent_50%)]"
            aria-hidden
          />
          <motion.div
            variants={heroContainer}
            initial="hidden"
            animate="visible"
            className="relative z-10 mx-auto w-full max-w-3xl px-6 text-center md:px-10"
          >
            <motion.p variants={fadeBlurUp} className={labelClass}>
              A supervisory surface for OS agents
            </motion.p>
            <motion.h1
              variants={fadeBlurUp}
              className="experience-poetry mt-12 text-[clamp(2.35rem,7.5vw,4.75rem)] font-light leading-[1.14] tracking-[-0.02em] text-[#0a0a0a] md:mt-14 md:leading-[1.1]"
            >
              Permission is not a setting.
              <br />
              <span className="text-neutral-800">It is a relationship.</span>
            </motion.h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.35, duration: 0.95, ease: easeLux }}
            className="absolute bottom-10 left-0 right-0 z-10 flex flex-col items-center gap-3 md:bottom-14"
          >
            <motion.span
              className={`${labelClass} text-forest-600/65`}
              animate={{ opacity: [0.65, 1, 0.65] }}
              transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
            >
              Scroll to explore
            </motion.span>
            <motion.div
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
            >
              <ArrowDown className="h-5 w-5 text-sage-600/70" strokeWidth={1.25} aria-hidden />
            </motion.div>
          </motion.div>
        </section>

        <section className="relative flex min-h-[88dvh] items-center justify-center bg-gradient-to-b from-[#f5f5f0] via-wash-peach/30 to-paper-2 px-6 py-24 md:px-12 md:py-28">
          <div className="relative z-10 mx-auto w-full max-w-2xl">
            <Verse
              lines={["You begin", "where the machine", "asks for a door."]}
              attribution="— premise"
              className="text-[clamp(1.65rem,4.8vw,2.85rem)] text-ink"
            />
          </div>
        </section>

        <section className="relative flex min-h-[88dvh] items-center justify-center bg-gradient-to-b from-forest-950 via-[#1a2420] to-forest-950 px-6 py-24 text-paper-2 md:px-12">
          <div
            className="pointer-events-none absolute inset-0 opacity-40 bg-[radial-gradient(ellipse_80%_60%_at_50%_30%,rgba(120,160,130,0.12),transparent_55%)]"
            aria-hidden
          />
          <div className="relative z-10 mx-auto w-full max-w-2xl">
            <Verse
              tone="dark"
              lines={[
                "Policy is the night",
                "with eyes enough",
                "to trace its own edge.",
              ]}
              attribution="— mediation"
              className="text-[clamp(1.6rem,4.5vw,2.75rem)] text-paper-2"
            />
          </div>
        </section>

        <section className="relative flex min-h-[85dvh] items-center justify-center bg-gradient-to-b from-paper-2 via-wash-mist/35 to-[#f5f5f0] px-6 py-28 md:px-16 md:py-32">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-10%" }}
            variants={verseBlockParent}
            className="relative z-10 mx-auto max-w-xl text-center"
          >
            <motion.div
              variants={verseLine}
              className="experience-poetry text-[clamp(1.2rem,3.2vw,1.65rem)] font-light leading-[1.62] tracking-[-0.012em] text-forest-800"
            >
              Risk arrives when nowhere else will hold it—when the path looks harmless, when the
              command sounds like help, when the weight of what you carry does not show on the
              prompt.
            </motion.div>
            <motion.p
              variants={fadeBlurUp}
              className={`mt-10 ${labelClass} text-forest-600/68`}
            >
              — hooks &amp; sandbox
            </motion.p>
          </motion.div>
        </section>

        {/* FAQ — centered editorial */}
        <section className="relative border-t border-stone-200/45 bg-[#f5f5f0] px-6 py-28 md:px-16 md:py-36">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-8%" }}
            variants={heroContainer}
            className="mx-auto max-w-2xl text-center"
          >
            <motion.h2
              variants={fadeBlurUp}
              className="font-display text-[clamp(1.95rem,4.5vw,3rem)] font-light leading-[1.08] tracking-[-0.02em] text-[#000000]"
            >
              Commonly asked
              <br />
              questions
            </motion.h2>
          </motion.div>

          <ul className="mx-auto mt-16 max-w-xl space-y-12 md:mt-20 md:space-y-14">
            {faqItems.map((item, i) => (
              <motion.li
                key={item.q}
                initial={{ opacity: 0, y: 26, filter: "blur(8px)" }}
                whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                viewport={{ once: true, margin: "-5%" }}
                transition={{ duration: 0.95, delay: i * 0.08, ease: easeLux }}
                className="text-center"
              >
                <h3 className="font-display text-[1.2rem] font-light leading-[1.2] tracking-[-0.015em] text-[#000000] md:text-[1.35rem]">
                  {item.q}
                </h3>
                <p className="mx-auto mt-4 max-w-lg font-sans text-[14px] leading-relaxed text-forest-700/88">
                  {item.a}
                </p>
                <motion.button
                  type="button"
                  className="mt-5 font-display text-[12px] font-medium tracking-wide text-forest-800 underline decoration-stone-400/70 underline-offset-[6px]"
                  whileHover={{ opacity: 0.75, scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  View
                </motion.button>
              </motion.li>
            ))}
          </ul>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.9, delay: 0.15, ease: easeLux }}
            className="mt-24 flex flex-col items-center gap-5"
          >
            <Link
              to="/dashboard"
              className="inline-flex min-w-[13rem] items-center justify-center border border-forest-900/90 bg-forest-950 px-9 py-3.5 font-sans text-[11px] font-semibold uppercase tracking-[0.26em] text-paper transition hover:bg-forest-900"
            >
              Enter the console
            </Link>
            <p className="font-sans text-[10px] uppercase tracking-[0.12em] text-forest-600/72">
              Mediation · hooks · heatmap · authority · audit · rollback
            </p>
          </motion.div>
        </section>

        <footer className="border-t border-stone-200/55 bg-paper-2/95 px-6 py-14 text-center md:px-12">
          <motion.button
            type="button"
            onClick={restart}
            className="inline-flex items-center gap-2 font-sans text-[11px] font-semibold uppercase tracking-[0.22em] text-forest-700 transition hover:text-ink"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
          >
            <RotateCcw className="h-4 w-4" strokeWidth={1.5} aria-hidden />
            Restart the experience
          </motion.button>
        </footer>
      </div>
    </div>
  );
}
