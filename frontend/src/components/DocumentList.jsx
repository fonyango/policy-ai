import { useState } from "react";

import { deleteDocument } from "../api";

function DocumentList({
    documents,
    loading,
    error,
    onDelete,
    canDelete = false,
}) {
    const [deleting, setDeleting] = useState("");
    const [deleteError, setDeleteError] = useState("");

    async function handleDelete(filename) {
        try {
            setDeleting(filename);
            setDeleteError("");

            await deleteDocument(filename);
            await onDelete();
        } catch (err) {
            setDeleteError(err.message);
        } finally {
            setDeleting("");
        }
    }

    if (loading) {
        return <p>Loading documents...</p>;
    }

    if (error) {
        return <p>{error}</p>;
    }

    return (
        <section>
            <h2>Documents</h2>

            {deleteError && <p>{deleteError}</p>}

            {documents.length === 0 ? (
                <p>No documents uploaded.</p>
            ) : (
                <ul>
                    {documents.map((document) => (
                        <li key={document.filename}>
                            <span>{document.filename}</span>

                            {canDelete && (
                                <button
                                    type="button"
                                    disabled={deleting === document.filename}
                                    onClick={() => handleDelete(document.filename)}
                                >
                                    {deleting === document.filename
                                        ? "Deleting..."
                                        : "Delete"}
                                </button>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}

export default DocumentList;