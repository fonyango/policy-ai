import { useRef, useState } from "react";

import { uploadDocument } from "../api";

function DocumentUpload({ onUpload }) {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");
    const fileInputRef = useRef(null);

    async function handleSubmit(event) {
        event.preventDefault();

        if (!file) {
            setError("Select a PDF file.");
            return;
        }

        try {
            setUploading(true);
            setError("");

            await uploadDocument(file);
            await onUpload();

            setFile(null);

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    }

    return (
        <section>
            <form onSubmit={handleSubmit}>
                <label className="file-picker">
                    <span className="file-picker-button">Choose PDF</span>

                    <span className="file-picker-name">
                        {file ? file.name : "No file selected"}
                    </span>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="application/pdf"
                        onChange={(event) =>
                            setFile(event.target.files?.[0] ?? null)
                        }
                    />
                </label>

                <button type="submit" disabled={uploading || !file}>
                    {uploading ? "Processing..." : "Upload PDF"}
                </button>

                {error && <p className="error">{error}</p>}
            </form>
        </section>
    );
}

export default DocumentUpload;