import Link from "next/link";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.main}>
      <section className={styles.hero}>
        <h1 className={styles.title}>Bryan Overbey</h1>
        <p className={styles.subtitle}>
          Software Engineer &amp; Builder
        </p>

        <div className={styles.grid}>
          <Link href="/fuel-receipt-sorter" className={styles.cardLink}>
            <div className={styles.card}>
              <h3>Fuel Receipt Sorter</h3>
              <p>Upload fleet fuel receipt PDFs and automatically sort pages by vehicle VIN.</p>
            </div>
          </Link>

          <div className={styles.card}>
            <h3>Projects</h3>
            <p>A collection of things I&apos;ve built and contributed to.</p>
          </div>

          <div className={styles.card}>
            <h3>About</h3>
            <p>Learn more about my background, skills, and interests.</p>
          </div>

          <div className={styles.card}>
            <h3>Contact</h3>
            <p>Get in touch for collaborations or just to say hello.</p>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        &copy; {new Date().getFullYear()} Bryan Overbey
      </footer>
    </main>
  );
}
