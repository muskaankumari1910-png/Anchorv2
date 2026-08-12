import React, { useState, useRef } from 'react';
import { Upload, FileText, File, X, CheckCircle, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  onUploadComplete?: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadResult, setUploadResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const supportedFormats = ['TXT', 'MD', 'DOCX', 'VTT'];
  const maxFileSize = 200; // MB

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check file size
      const fileSizeMB = file.size / (1024 * 1024);
      if (fileSizeMB > maxFileSize) {
        setErrorMessage(`File too large: ${fileSizeMB.toFixed(1)}MB. Maximum: ${maxFileSize}MB`);
        setUploadStatus('error');
        return;
      }

      setSelectedFile(file);
      setUploadStatus('idle');
      setErrorMessage('');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) {
      const fileSizeMB = file.size / (1024 * 1024);
      if (fileSizeMB > maxFileSize) {
        setErrorMessage(`File too large: ${fileSizeMB.toFixed(1)}MB. Maximum: ${maxFileSize}MB`);
        setUploadStatus('error');
        return;
      }

      setSelectedFile(file);
      setUploadStatus('idle');
      setErrorMessage('');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setUploadStatus('idle');
      setErrorMessage('');

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/ingest', {
        method: 'POST',
        headers: {
          'X-Workspace-ID': 'default'
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail?.message || errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      
      setUploadStatus('success');
      setUploadResult(result);
      
      // Clear file after 2 seconds
      setTimeout(() => {
        setSelectedFile(null);
        setUploadStatus('idle');
        setUploadResult(null);
        if (onUploadComplete) {
          onUploadComplete();
        }
      }, 2000);

    } catch (error: any) {
      setUploadStatus('error');
      setErrorMessage(error.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setErrorMessage('');
    setUploadResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Upload Document</h3>
        <p className="text-sm text-gray-500">
          Upload transcripts or requirement documents for extraction
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          selectedFile
            ? 'border-blue-300 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
        }`}
      >
        {!selectedFile ? (
          <div>
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 mb-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Click to upload
              </button>{' '}
              or drag and drop
            </p>
            <p className="text-sm text-gray-500 mb-3">
              Supported: {supportedFormats.join(', ')} or transcript files
            </p>
            <p className="text-xs text-gray-400">Maximum file size: {maxFileSize}MB</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-center space-x-3">
              {selectedFile.name.endsWith('.txt') && <FileText className="w-8 h-8 text-blue-600" />}
              {selectedFile.name.endsWith('.md') && <File className="w-8 h-8 text-blue-600" />}
              {selectedFile.name.endsWith('.docx') && <File className="w-8 h-8 text-blue-600" />}
              {selectedFile.name.endsWith('.vtt') && <File className="w-8 h-8 text-blue-600" />}
              {!selectedFile.name.match(/\.(txt|md|docx|vtt)$/) && <File className="w-8 h-8 text-blue-600" />}
              
              <div className="text-left">
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
              </div>
            </div>

            {uploadStatus === 'idle' && !uploading && (
              <div className="flex justify-center space-x-3">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Upload
                </button>
                <button
                  onClick={handleClear}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {uploading && (
              <div className="flex items-center justify-center space-x-2 text-blue-600">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <span>Uploading...</span>
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="flex items-center justify-center space-x-2 text-green-600">
                <CheckCircle className="w-5 h-5" />
                <span>Upload successful! ({uploadResult?.segments?.length || 0} segments)</span>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="text-red-600">
                <div className="flex items-center justify-center space-x-2 mb-2">
                  <AlertCircle className="w-5 h-5" />
                  <span>Upload failed</span>
                </div>
                <p className="text-sm">{errorMessage}</p>
                <button
                  onClick={handleClear}
                  className="mt-2 text-sm text-blue-600 hover:underline"
                >
                  Try again
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.docx,.vtt"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Info */}
      <div className="mt-4 text-xs text-gray-500 space-y-1">
        <p>• TXT: Plain text documents or speaker-labeled transcripts</p>
        <p>• MD: Markdown documents</p>
        <p>• DOCX: Microsoft Word documents</p>
        <p>• VTT: WebVTT transcript files with timestamps</p>
      </div>
    </div>
  );
};

export default FileUpload;