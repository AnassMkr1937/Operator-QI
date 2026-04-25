function App() {
  return (
    <main className="container">
      <h1>OPERATOR-QI</h1>
      <p>Plateforme de matching opérateurs-missions</p>
      <p className="status">
        Backend:{" "}
        <a href="/api/health" target="_blank" rel="noreferrer">
          /api/health
        </a>
      </p>
    </main>
  );
}

export default App;
