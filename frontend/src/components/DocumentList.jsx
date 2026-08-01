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

    async function handleDelete(documentId) {
        try {
            setDeleting(documentId);
            setDeleteError("");

            await deleteDocument(documentId);
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
                        <li key={document.id}>
                            <span>{document.filename}</span>

                            {canDelete && (
                                <button
                                    type="button"
                                    disabled={deleting === document.id}
                                    onClick={() => handleDelete(document.id)}
                                >
                                    {deleting === document.id
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