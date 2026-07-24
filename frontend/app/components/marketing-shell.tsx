"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import stlafLogo from "../images/logo.png";

/* ============================================================
   SHARED ICONS
   ============================================================ */

export function ScalesIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 3v18M5 7h14M5 7l-3 6a3 3 0 006 0l-3-6zM19 7l-3 6a3 3 0 006 0l-3-6zM8 21h8" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="4.5" strokeWidth="1.7" />
      <path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 14.5A8.5 8.5 0 119.5 4 6.5 6.5 0 0020 14.5z" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  );
}

function BookIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 004 15.5v-10zM4 15.5A2.5 2.5 0 016.5 18H20" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function BoltIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function RobotIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <rect x="5" y="8" width="14" height="11" rx="2.5" strokeWidth="1.6" />
      <path d="M9 13h.01M15 13h.01M9 17h6M12 8V4m0 0h2m-2 0H10" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <circle cx="10.5" cy="10.5" r="6.5" strokeWidth="1.6" />
      <path d="M20 20l-4.8-4.8" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 5h16v11H8l-4 4V5z" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 3l7 3v6c0 4.5-3 7.7-7 9-4-1.3-7-4.5-7-9V6l7-3z" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 9h3V6h-3c-1.7 0-3 1.3-3 3v2H9v3h2v6h3v-6h2.5l.5-3H14V9.5c0-.3.2-.5.5-.5z" />
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M6.5 8.5h-3v10h3v-10zM5 3.5a1.75 1.75 0 100 3.5 1.75 1.75 0 000-3.5zM10.5 8.5h-3v10h3v-5.3c0-1.6.8-2.5 2.1-2.5 1.2 0 1.9.8 1.9 2.5v5.3h3v-6c0-3-1.6-4.4-3.7-4.4-1.7 0-2.5.9-2.9 1.6h-.1V8.5h-.3z" />
    </svg>
  );
}

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <rect x="3.5" y="3.5" width="17" height="17" rx="4.5" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="4" strokeWidth="1.6" />
      <circle cx="17.2" cy="6.8" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="5" width="18" height="14" rx="2" strokeWidth="1.6" />
      <path d="M3 7l9 6 9-6" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function GlobeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="9" strokeWidth="1.6" />
      <path d="M3 12h18M12 3c2.5 2.7 3.8 6 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-6-3.8-9s1.3-6.3 3.8-9z" strokeWidth="1.6" />
    </svg>
  );
}

/* ============================================================
   SHARED THEME HOOK - each page that mounts this reads/writes the
   same document.documentElement[data-theme] + localStorage key set
   by the blocking script in layout.tsx, so theme stays consistent
   across page navigations without needing global state/context.

   DEFENSIVE FALLBACK: if data-theme was never set (e.g. layout.tsx's
   blocking pre-hydration script is missing or was reverted), every
   themed CSS variable would stay unresolved indefinitely - nothing
   else would ever call setAttribute until the user manually clicks
   the toggle. This hook checks for that on mount and self-corrects
   immediately rather than silently staying broken. The CSS also has
   its own independent fallback (:root baseline values in
   globals.css) as a second layer - this hook fixes it for real
   (writes the actual attribute + persists it), the CSS fallback is
   just the safety net for the brief window before this runs.
   ============================================================ */

export function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const current = document.documentElement.getAttribute("data-theme");
    if (current === "light" || current === "dark") {
      setTheme(current);
      return;
    }

    // No attribute set at all - determine a sensible default the
    // same way the blocking script in layout.tsx is supposed to,
    // and apply it now instead of leaving things unresolved.
    let fallback: "dark" | "light" = "dark";
    try {
      const stored = localStorage.getItem("stlaf-theme");
      if (stored === "light" || stored === "dark") {
        fallback = stored;
      } else if (window.matchMedia("(prefers-color-scheme: light)").matches) {
        fallback = "light";
      }
    } catch {
      // localStorage/matchMedia unavailable - fall back to dark.
    }
    document.documentElement.setAttribute("data-theme", fallback);
    setTheme(fallback);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("stlaf-theme", next);
    } catch {
      // localStorage unavailable (e.g. private browsing) - theme
      // still works for this session, just won't persist.
    }
  };

  return { theme, toggleTheme };
}

/* ============================================================
   ABOUT SECTION - fade-in-on-scroll via native IntersectionObserver
   ============================================================ */

function useInView<T extends HTMLElement>(threshold = 0.15) {
  const ref = useRef<T>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, isVisible };
}

const FEATURES = [
  { icon: <BookIcon />, title: "Official Knowledge Base", body: "Answers are generated using trusted Philippine labor law references and official documents." },
  { icon: <BoltIcon />, title: "Instant Responses", body: "Receive answers within seconds instead of searching through lengthy legal texts." },
  { icon: <RobotIcon />, title: "AI-Powered Assistant", body: "Uses AI to understand natural language questions and provide relevant responses." },
  { icon: <SearchIcon />, title: "Intelligent Search", body: "Find information about wages, leave benefits, overtime pay, separation pay, working hours, and other labor-related topics." },
  { icon: <ChatIcon />, title: "Natural Conversations", body: "Ask questions in plain English without needing legal terminology." },
  { icon: <ShieldIcon />, title: "Reliable Information", body: "Designed to provide accurate and consistent responses based on the chatbot's knowledge base." },
];

function AboutSection() {
  const { ref: aboutRef, isVisible: aboutVisible } = useInView<HTMLDivElement>();

  return (
    <section id="about-section" className="about-section">
      <div className="about-bg-motif" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M12 2v20M4 6h16M4 6l-3.2 6.4a3.4 3.4 0 006.6 0L4 6zM20 6l-3.2 6.4a3.4 3.4 0 006.6 0L20 6zM7 22h10" strokeWidth="0.4" />
        </svg>
      </div>

      <div ref={aboutRef} className={`about-content ${aboutVisible ? "in-view" : ""}`}>
        <h2 className="about-heading">
          Your Intelligent <span className="accent">Philippine Labor Law</span> Assistant
        </h2>
        <p className="about-intro">
          STLAF&apos;s Labor Law Assistant is designed to help you quickly access reliable
          information about Philippine labor laws using AI and official legal references -
          offering instant, easy-to-understand answers grounded in official documents,
          built for employees, employers, HR professionals, students, and researchers alike.
        </p>

        <div className="feature-grid">
          {FEATURES.map((feature) => (
            <div className="feature-card" key={feature.title}>
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================
   FOOTER
   ============================================================ */

function SiteFooter({ onStartClick }: { onStartClick: () => void }) {
  return (
    <footer className="site-footer">
      <div className="footer-grid">
        <div className="footer-col">
          <Image src={stlafLogo} alt="STLAF" width={40} height={40} className="navbar-logo-img" />
          <p className="footer-tagline">
            Redefining legal solutions through excellence and commitment.
          </p>
          <div className="footer-socials">
            <a href="#" aria-label="Facebook" title="Add real Facebook URL">
              <FacebookIcon />
            </a>
            <a href="mailto:legal@sadsadtamesislaw.com" aria-label="Email">
              <MailIcon />
            </a>
            <a href="#" aria-label="LinkedIn" title="Add real LinkedIn URL">
              <LinkedInIcon />
            </a>
            <a href="#" aria-label="Instagram" title="Add real Instagram URL">
              <InstagramIcon />
            </a>
            <a href="https://www.sadsadtamesislaw.com" aria-label="Website" title="Verify this URL is correct" target="_blank" rel="noopener noreferrer">
              <GlobeIcon />
            </a>
          </div>
        </div>

        <div className="footer-col">
          <h4>Office Details</h4>
          <p className="footer-label">Address</p>
          <p>7F Victoria Sports Tower, EDSA, South Triangle, Quezon City, 1103 Metro Manila, Philippines</p>
          <p className="footer-hours">Mon to Fri: 8:00 AM – 5:00 PM (UTC+8)</p>
          <p className="footer-label">Accounting Department</p>
          <p>(632) 8463-5094</p>
          <p className="footer-label">Corporate Department</p>
          <p>(632) 8463-5076 &nbsp;/&nbsp; (+63) 967-300-2449</p>
          <p className="footer-label">Human Resources Department</p>
          <p>(+63) 967-086-8907</p>
          <p className="footer-label">Litigation Department</p>
          <p>(632) 8463-4941 &nbsp;/&nbsp; (+63) 948-961-2397</p>
          <p><a href="mailto:legal@sadsadtamesislaw.com">legal@sadsadtamesislaw.com</a></p>
          <p><a href="mailto:hrrecruitment@sadsadtamesislaw.com">hrrecruitment@sadsadtamesislaw.com</a></p>
        </div>

        <div className="footer-col">
          <h4>Quick Links</h4>
          <a href="/">Home</a>
          <a href="/#about-section" onClick={(e) => { e.preventDefault(); document.getElementById("about-section")?.scrollIntoView({ behavior: "smooth" }); }}>About the Chatbot</a>
          <a href="#" onClick={(e) => { e.preventDefault(); onStartClick(); }}>Start Chat</a>
          <a href="mailto:legal@sadsadtamesislaw.com">Contact</a>
          <a href="#" title="Add real Privacy Policy page when available">Privacy Policy</a>
          <a href="#" title="Add real Terms of Service page when available">Terms of Service</a>
        </div>

        <div className="footer-col">
          <h4>Practice Areas</h4>
          <span>Corporate &amp; Special Projects</span>
          <span>Litigation</span>
          <span>Tax &amp; Estate</span>
          <span>Property Settlements</span>
          <span>Corporation &amp; Stocks</span>
          <span>Prosecution &amp; Defense</span>
          <span>Business Law &amp; Compliance</span>
        </div>
      </div>

      <div className="footer-bottom">
        <span>Copyright © {new Date().getFullYear()} Sadsad Tamesis Legal and Accountancy Firm — All Rights Reserved.</span>
        <span>Powered by Sadsad Tamesis Legal and Accountancy Firm</span>
      </div>
    </footer>
  );
}

/* ============================================================
   MARKETING SHELL - the full page chrome. `children` renders into
   the hero-right slot (the chat card on the home page, or an auth
   form card on login/register/forgot-password).
   ============================================================ */

type MarketingShellProps = {
  children: React.ReactNode;
  showLogout?: boolean;
  onLogout?: () => void;
};

export default function MarketingShell({ children, showLogout = false, onLogout }: MarketingShellProps) {
  const { theme, toggleTheme } = useTheme();

  // Generic "focus the primary interactive element" behavior - works
  // for the chat input on the home page AND any auth form's first
  // input, since both live inside .hero-right, without needing a
  // separate callback prop wired through every page.
  const focusPrimaryElement = () => {
    const el = document.querySelector<HTMLElement>(".hero-right input");
    el?.focus();
  };

  return (
    <>
      <div className="ambient-bg" aria-hidden="true">
        <div className="dot-grid" />
      </div>

      <nav className="navbar">
        <div className="navbar-left">
          <Image src={stlafLogo} alt="STLAF" width={32} height={32} className="navbar-logo-img" priority />
          <span className="navbar-brand-name">STLAF</span>
        </div>
        <div className="navbar-right">
          <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
          {showLogout && (
            <button className="logout-btn" onClick={onLogout}>Logout</button>
          )}
        </div>
      </nav>

      <div className="hero-shell">
        <div className="hero-left">
          <div className="hero-brand">
            <Image src={stlafLogo} alt="STLAF" width={44} height={44} className="navbar-logo-img" />
            <span className="hero-brand-name">STLAF</span>
          </div>

          <h1 className="hero-headline">
            Philippine Labor Law, <span className="accent">answered instantly.</span>
          </h1>

          <p className="hero-subtext">
            Get accurate, AI-powered answers about Philippine labor laws, employee rights,
            wages, benefits, leave policies, and workplace regulations - grounded in official
            documents only.
          </p>

          <div className="hero-cta-row">
            <button className="btn-primary" onClick={focusPrimaryElement}>
              Start Chatting
            </button>
            <button className="btn-secondary" onClick={() => document.getElementById("about-section")?.scrollIntoView({ behavior: "smooth" })}>
              Learn More
            </button>
          </div>
        </div>

        <div className="hero-right">
          {children}
        </div>
      </div>

      <AboutSection />
      <SiteFooter onStartClick={focusPrimaryElement} />
    </>
  );
}
