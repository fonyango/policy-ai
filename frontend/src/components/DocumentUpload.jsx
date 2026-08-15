import { useRef, useState } from "react";

import { uploadDocument } from "../api";

function DocumentUpload({ onUpload }) {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");
    const fileInputRef = useRef(null);

    async function handleFileChange(event) {
        const selectedFile = event.target.files?.[0];

        if (!selectedFile) {
            return;
        }

        try {
            setUploading(true);
            setError("");

            await uploadDocument(selectedFile);
            await onUpload();
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    }

    return (
        <div className="document-upload">
            <button
                type="button"
                className="upload-button"
                disabled={uploading}
                onClick={() => fileInputRef.current?.click()}
            >
                {uploading ? "Processing..." : "+ Upload PDF"}
            </button>

            <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                hidden
                onChange={handleFileChange}
            />

            {error && <p className="error">{error}</p>}
        </div>
    );
}

export default DocumentUpload;