import { useState } from "react";

import { login, register } from "../api";

export default function Auth({ onAuthenticated }) {
    const [mode, setMode] = useState("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setIsSubmitting(true);

        try {
            if (mode === "register") {
                await register(email, password);
            }

            const result = await login(email, password);
            onAuthenticated(result.user);
        } catch (error) {
            setError(error.message);
        } finally {
            setIsSubmitting(false);
        }
    }

    function switchMode() {
        setMode((current) =>
            current === "login" ? "register" : "login"
        );
        setError("");
    }

    return (
        <main className="auth-page">
            <section className="auth-card">
                <div className="auth-heading">
                    <h1>PolicyAI</h1>
                    <p>
                        {mode === "login"
                            ? "Sign in to access your documents."
                            : "Create an account to get started."}
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    <label>
                        Email
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            required
                            autoComplete="email"
                        />
                    </label>

                    <label>
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            required
                            minLength={8}
                            autoComplete={
                                mode === "login"
                                    ? "current-password"
                                    : "new-password"
                            }
                        />
                    </label>

                    {error && <p className="auth-error">{error}</p>}

                    <button type="submit" disabled={isSubmitting}>
                        {isSubmitting
                            ? "Please wait..."
                            : mode === "login"
                                ? "Sign in"
                                : "Create account"}
                    </button>
                </form>

                <button
                    type="button"
                    className="auth-switch"
                    onClick={switchMode}
                >
                    {mode === "login"
                        ? "Create an account"
                        : "Already have an account? Sign in"}
                </button>
            </section>
        </main>
    );
}