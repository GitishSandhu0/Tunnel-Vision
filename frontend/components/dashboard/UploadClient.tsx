"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud,
  FileArchive,
  FileJson,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { uploadFile } from "@/lib/api";
import type { UploadJob } from "@/types";
import Button from "@/components/ui/Button";

interface FileEntry {
  file: File;
  id: string;
  status: "idle" | "uploading" | "success" | "error";
  progress: number;
  error?: string;
  job?: UploadJob;
}

function FileIcon({ name }: { name: string }) {
  if (name.endsWith(".zip")) {
    return <FileArchive className="w-5 h-5 text-blue-400" />;
  }
  return <FileJson className="w-5 h-5 text-purple-400" />;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadClient() {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    const newEntries: FileEntry[] = accepted.map((file) => ({
      file,
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      status: "idle",
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newEntries]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/zip": [".zip"],
      "application/x-zip-compressed": [".zip"],
      "application/json": [".json"],
    },
    maxSize: 100 * 1024 * 1024, // 100 MB
    disabled: uploading,
  });

  function removeFile(id: string) {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }

  async function handleUpload() {
    const idleFiles = files.filter((f) => f.status === "idle");
    if (!idleFiles.length) return;

    setUploading(true);

    await Promise.all(
      idleFiles.map(async (entry) => {
        // mark uploading
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id ? { ...f, status: "uploading" } : f
          )
        );

        const result = await uploadFile(entry.file, (pct) => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === entry.id ? { ...f, progress: pct } : f
            )
          );
        });

        if (result.error) {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === entry.id
                ? { ...f, status: "error", error: result.error, progress: 0 }
                : f
            )
          );
        } else {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === entry.id
                ? { ...f, status: "success", progress: 100 }
                : f
            )
          );
        }
      })
    );

    setUploading(false);
  }

  const idleCount = files.filter((f) => f.status === "idle").length;

  return (
    <div className="space-y-5">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer p-10 text-center
          ${
            isDragActive
              ? "border-blue-400 bg-blue-500/10 shadow-[0_0_30px_rgba(59,130,246,0.2)]"
              : "border-white/15 hover:border-blue-400/50 hover:bg-white/3"
          }
          ${uploading ? "opacity-60 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          <motion.div
            animate={{ y: isDragActive ? -4 : 0 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center"
          >
            <UploadCloud
              className={`w-8 h-8 ${
                isDragActive ? "text-blue-400" : "text-white/40"
              }`}
            />
          </motion.div>

          {isDragActive ? (
            <div>
              <p className="text-blue-400 font-semibold text-lg">
                Drop your files here
              </p>
            </div>
          ) : (
            <div>
              <p className="text-white/70 font-medium text-base mb-1">
                Drag &amp; drop files here, or{" "}
                <span className="text-blue-400">browse</span>
              </p>
              <p className="text-white/30 text-sm">
                Accepts .zip and .json · Max 100 MB per file
              </p>
            </div>
          )}
        </div>
      </div>

      {/* File list */}
      <AnimatePresence initial={false}>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="space-y-2"
          >
            <h3 className="text-sm font-medium text-white/60 mb-3">
              Files ({files.length})
            </h3>
            {files.map((entry) => (
              <motion.div
                key={entry.id}
                layout
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={{ duration: 0.25 }}
                className="glass rounded-xl p-4"
              >
                <div className="flex items-center gap-3">
                  <FileIcon name={entry.file.name} />

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {entry.file.name}
                    </p>
                    <p className="text-xs text-white/30">
                      {formatBytes(entry.file.size)}
                    </p>
                  </div>

                  {/* Status icon */}
                  {entry.status === "idle" && (
                    <button
                      onClick={() => removeFile(entry.id)}
                      className="text-white/30 hover:text-white/60 transition-colors p-1"
                      aria-label="Remove file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                  {entry.status === "uploading" && (
                    <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                  )}
                  {entry.status === "success" && (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  )}
                  {entry.status === "error" && (
                    <AlertCircle className="w-4 h-4 text-red-400" />
                  )}
                </div>

                {/* Progress bar */}
                {entry.status === "uploading" && (
                  <div className="mt-3">
                    <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${entry.progress}%` }}
                        transition={{ duration: 0.2 }}
                      />
                    </div>
                    <p className="text-xs text-white/30 mt-1 text-right">
                      {entry.progress}%
                    </p>
                  </div>
                )}

                {/* Error message */}
                {entry.status === "error" && entry.error && (
                  <p className="mt-2 text-xs text-red-400">{entry.error}</p>
                )}

                {/* Success message */}
                {entry.status === "success" && (
                  <p className="mt-2 text-xs text-green-400">
                    Uploaded successfully — processing in background
                  </p>
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload button */}
      {idleCount > 0 && (
        <Button
          variant="primary"
          size="md"
          loading={uploading}
          onClick={handleUpload}
          icon={<UploadCloud className="w-4 h-4" />}
        >
          Upload {idleCount} file{idleCount > 1 ? "s" : ""}
        </Button>
      )}
    </div>
  );
}
