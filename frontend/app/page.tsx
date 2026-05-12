import Chat from "@/components/Chat";
import Header from "@/components/Header";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col">
      <Header />
      <Chat />
      <footer className="border-t border-stone-200 px-4 py-3 text-center text-xs text-stone-500 dark:border-stone-800">
        Unofficial fan content. Card data via{" "}
        <a className="underline" href="https://scryfall.com" target="_blank" rel="noreferrer">
          Scryfall
        </a>
        . Portions © Wizards of the Coast LLC.
      </footer>
    </main>
  );
}
