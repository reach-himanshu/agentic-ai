import React, { useState } from 'react';
import {
    Upload,
    Search,
    Database,
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Globe,
    Tag,
    Layers
} from 'lucide-react';
import { Button, Card, Badge } from '../components/ui';

export const KnowledgeHub: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'upload' | 'search'>('upload');
    const [file, setFile] = useState<File | null>(null);
    const [url, setUrl] = useState('');
    const [domain, setDomain] = useState('general');
    const [partition, setPartition] = useState('knowledge');
    const [isProcessing, setIsProcessing] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleFileUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setIsProcessing(true);
        setStatus(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`http://localhost:8001/ingest/file?domain=${domain}&partition=${partition}`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setStatus({ type: 'success', message: `Successfully ingested ${data.chunks} chunks from ${file.name}` });
                setFile(null);
            } else {
                throw new Error('Ingestion failed');
            }
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setIsProcessing(false);
        }
    };

    const handleUrlIngest = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url) return;

        setIsProcessing(true);
        setStatus(null);

        try {
            const response = await fetch(`http://localhost:8001/ingest/url?url=${encodeURIComponent(url)}&domain=${domain}`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                setStatus({ type: 'success', message: `Successfully ingested ${data.chunks} chunks from web page` });
                setUrl('');
            } else {
                throw new Error('URL ingestion failed');
            }
        } catch (err: any) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setIsProcessing(false);
        }
    };

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery) return;

        setIsProcessing(true);
        try {
            const response = await fetch(`http://localhost:8001/search?query=${encodeURIComponent(searchQuery)}`);
            if (response.ok) {
                const data = await response.json();
                setResults(data.results);
            }
        } catch (err) {
            console.error('Search failed', err);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <header className="mb-8 border-b border-white/10 pb-6">
                <div className="flex items-center gap-3 mb-2">
                    <Database className="text-[var(--color-accent-primary)]" size={28} />
                    <h1 className="text-3xl font-bold">Knowledge Hub</h1>
                </div>
                <p className="text-muted">Manage enterprise knowledge, ingestion, and semantic retrieval partitions.</p>
            </header>

            <div className="flex gap-4 mb-8 bg-white/5 p-1 rounded-lg w-fit">
                <button
                    className={`px-6 py-2 rounded-md transition-all ${activeTab === 'upload' ? 'bg-[var(--color-accent-primary)] text-white font-bold shadow-lg' : 'hover:bg-white/10 text-muted'}`}
                    onClick={() => setActiveTab('upload')}
                >
                    Ingest Content
                </button>
                <button
                    className={`px-6 py-2 rounded-md transition-all ${activeTab === 'search' ? 'bg-[var(--color-accent-primary)] text-white font-bold shadow-lg' : 'hover:bg-white/10 text-muted'}`}
                    onClick={() => setActiveTab('search')}
                >
                    Search Playground
                </button>
            </div>

            {status && (
                <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 border shadow-sm ${status.type === 'success' ? 'bg-success/10 border-success/30 text-success' : 'bg-danger/10 border-danger/30 text-danger'}`}>
                    {status.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                    <span className="font-medium">{status.message}</span>
                </div>
            )}

            {activeTab === 'upload' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <Card className="p-6 border-white/10 bg-white/[0.02]">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <Upload size={20} className="text-[var(--color-accent-primary)]" />
                            Document Upload
                        </h2>
                        <form onSubmit={handleFileUpload} className="space-y-6">
                            <div className="space-y-4">
                                <div className="p-8 border-2 border-dashed border-white/10 rounded-xl bg-white/[0.02] flex flex-col items-center justify-center gap-4 hover:border-[var(--color-accent-primary)] transition-colors cursor-pointer relative">
                                    <input
                                        type="file"
                                        className="absolute inset-0 opacity-0 cursor-pointer"
                                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                                        accept=".pdf,.docx,.txt"
                                    />
                                    <div className="p-4 bg-white/5 rounded-full">
                                        <FileText size={32} className="text-muted" />
                                    </div>
                                    <div className="text-center">
                                        <p className="font-medium">{file ? file.name : 'Click to upload or drag and drop'}</p>
                                        <p className="text-xs text-muted mt-1 text-muted">PDF, DOCX, TXT up to 10MB</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
                                            <Tag size={12} /> Domain
                                        </label>
                                        <select
                                            className="w-full bg-white/5 border border-white/10 rounded-md p-2 outline-none focus:border-[var(--color-accent-primary)] transition-all"
                                            value={domain}
                                            onChange={(e) => setDomain(e.target.value)}
                                        >
                                            <option value="general">General</option>
                                            <option value="HR">HR</option>
                                            <option value="Finance">Finance</option>
                                            <option value="IT">IT</option>
                                            <option value="Legal">Legal</option>
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
                                            <Layers size={12} /> Partition
                                        </label>
                                        <select
                                            className="w-full bg-white/5 border border-white/10 rounded-md p-2 outline-none focus:border-[var(--color-accent-primary)] transition-all"
                                            value={partition}
                                            onChange={(e) => setPartition(e.target.value)}
                                        >
                                            <option value="knowledge">Knowledge Base</option>
                                            <option value="sys_rules">System Rules</option>
                                            <option value="policies">Policies</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <Button
                                type="submit"
                                fullWidth
                                disabled={!file || isProcessing}
                                className="h-12 flex items-center justify-center gap-2"
                            >
                                {isProcessing ? <Loader2 className="animate-spin" size={20} /> : 'Process Document'}
                            </Button>
                        </form>
                    </Card>

                    <Card className="p-6 border-white/10 bg-white/[0.02]">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <Globe size={20} className="text-[var(--color-accent-primary)]" />
                            URL Crawler
                        </h2>
                        <form onSubmit={handleUrlIngest} className="space-y-6">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold uppercase tracking-wider text-muted">Web URL</label>
                                    <div className="relative">
                                        <Globe className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={16} />
                                        <input
                                            type="url"
                                            placeholder="https://firm-portal.com/policy..."
                                            className="w-full bg-white/5 border border-white/10 rounded-md p-3 pl-10 outline-none focus:border-[var(--color-accent-primary)] transition-all"
                                            value={url}
                                            onChange={(e) => setUrl(e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold uppercase tracking-wider text-muted">Domain Tag</label>
                                    <select
                                        className="w-full bg-white/5 border border-white/10 rounded-md p-2 outline-none focus:border-[var(--color-accent-primary)] transition-all"
                                        value={domain}
                                        onChange={(e) => setDomain(e.target.value)}
                                    >
                                        <option value="web">Web Resource</option>
                                        <option value="HR">HR</option>
                                        <option value="IT">IT</option>
                                    </select>
                                </div>
                            </div>
                            <Button
                                type="submit"
                                fullWidth
                                variant="secondary"
                                disabled={!url || isProcessing}
                                className="h-12 flex items-center justify-center gap-2"
                            >
                                {isProcessing ? <Loader2 className="animate-spin" size={20} /> : 'Crawl Page'}
                            </Button>
                        </form>
                    </Card>
                </div>
            ) : (
                <div className="space-y-6">
                    <Card className="p-6 border-white/10 bg-white/[0.02]">
                        <form onSubmit={handleSearch} className="flex gap-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={20} />
                                <input
                                    type="text"
                                    className="w-full bg-white/5 border border-white/10 rounded-lg p-3 pl-12 outline-none focus:border-[var(--color-accent-primary)]"
                                    placeholder="Ask anything about business domains or system rules..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <Button type="submit" disabled={isProcessing} className="px-8">
                                {isProcessing ? <Loader2 className="animate-spin" size={20} /> : 'Search'}
                            </Button>
                        </form>
                    </Card>

                    <div className="space-y-4">
                        {results.length > 0 ? results.map((res, i) => (
                            <Card key={i} className="p-6 border-white/5 hover:border-white/20 transition-all bg-white/[0.01]">
                                <div className="flex justify-between items-start mb-4">
                                    <Badge variant="info" className="uppercase tracking-tighter text-[10px]">
                                        Score: {res.metadata.score.toFixed(4)}
                                    </Badge>
                                    <div className="flex items-center gap-2 text-xs text-muted">
                                        <FileText size={14} />
                                        <span>{res.metadata.source}</span>
                                        <Badge variant="outline" className="opacity-50">{res.metadata.domain}</Badge>
                                    </div>
                                </div>
                                <p className="text-sm leading-relaxed opacity-90">{res.content}</p>
                            </Card>
                        )) : !isProcessing && (
                            <div className="py-20 text-center text-muted opacity-30">
                                <Search size={48} className="mx-auto mb-4" />
                                <p>Search results will appear here</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
