import { useState } from "react";

import { askQuestion } from "../api";

const suggestions = [
    "Summarize the key obligations",
    "Explain the procurement thresholds",
    "What are the open tender requirements?",
];

function Chat({ documents }) {
    const [question, setQuestion] = useState("");
    const [filename, setFilename] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function submitQuestion(value) {
        const trimmedQuestion = value.trim();

        if (!trimmedQuestion || loading) {
            return;
        }

        setMessages((current) => [
            ...current,
            {
                role: "user",
                content: trimmedQuestion,
            },
        ]);

        setQuestion("");
        setError("");
        setLoading(true);

        try {
            const result = await askQuestion(
                trimmedQuestion,
                filename || null
            );

            setMessages((current) => [
                ...current,
                {
                    role: "assistant",
                    content: result.answer,
                    sources: result.sources,
                },
            ]);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    function handleSubmit(event) {
        event.preventDefault();
        submitQuestion(question);
    }

    return (
        <section className="chat-shell">
            <div className="conversation">
                {messages.length === 0 ? (
                    <div className="welcome-state">
                        <div className="welcome-mark">P</div>

                        <h1>
                            Understand policy.
                            <span> Make better decisions.</span>
                        </h1>

                        <p>
                            Ask questions across your uploaded policy documents and receive
                            grounded answers with source references.
                        </p>

                        <div className="suggestion-grid">
                            {suggestions.map((suggestion) => (
                                <button
                                    key={suggestion}
                                    type="button"
                                    onClick={() => submitQuestion(suggestion)}
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="message-list">
                        {messages.map((message, index) => (
                            <article
                                key={`${message.role}-${index}`}
                                className={`message ${message.role}`}
                            >
                                <div className="message-label">
                                    {message.role === "user" ? "You" : "PolicyAI"}
                                </div>

                                <div className="message-body">
                                    <p>{message.content}</p>

                                    {message.sources?.length > 0 && (
                                        <div className="source-list">
                                            <span>Sources</span>

                                            {message.sources.map((source, sourceIndex) => (
                                                <div
                                                    className="source-item"
                                                    key={`${source.document_title}-${source.page_start}-${sourceIndex}`}
                                                >
                                                    <strong>{source.document_title}</strong>

                                                    <small>
                                                        Pages {source.page_start}
                                                        {source.page_end !== source.page_start &&
                                                            `–${source.page_end}`}
                                                    </small>

                                                    {source.section && <p>{source.section}</p>}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </article>
                        ))}

                        {loading && (
                            <article className="message assistant">
                                <div className="message-label">PolicyAI</div>

                                <div className="typing-indicator">
                                    <span />
                                    <span />
                                    <span />
                                </div>
                            </article>
                        )}
                    </div>
                )}
            </div>

            {error && <p className="error">{error}</p>}

            <form className="composer" onSubmit={handleSubmit}>
                <textarea
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask PolicyAI anything about your documents..."
                    rows="2"
                />

                <div className="composer-toolbar">
                    <select
                        value={filename}
                        onChange={(event) => setFilename(event.target.value)}
                    >
                        <option value="">All documents</option>

                        {documents.map((document) => (
                            <option key={document.id} value={document.id}>
                                {document.filename}
                            </option>
                        ))}
                    </select>

                    <button
                        type="submit"
                        disabled={loading || !question.trim()}
                        aria-label="Send question"
                    >
                        ↑
                    </button>
                </div>
            </form>

            <p className="assistant-notice">
                PolicyAI may make mistakes. Verify important information against the
                cited source.
            </p>
        </section>
    );
}

export default Chat;