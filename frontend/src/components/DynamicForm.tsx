import React, { useState } from 'react';
import { Button } from './ui';

export interface DynamicFormField {
    key: string;
    label: string;
    value: any;
    type?: string;
    options?: { label: string; value: any }[];
    editable: boolean;
}

export interface DynamicFormProps {
    title: string;
    fields: DynamicFormField[];
    submitAction: string;
    onSubmit: (values: any) => void;
    isLoading?: boolean;
    disabled?: boolean;
}

export const DynamicForm: React.FC<DynamicFormProps> = ({ title, fields, onSubmit, isLoading, disabled = false }) => {
    const [formValues, setFormValues] = useState<Record<string, any>>(
        fields.reduce((acc, field) => ({ ...acc, [field.key]: field.value }), {})
    );

    const handleChange = (key: string, value: any) => {
        setFormValues(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formValues);
    };

    return (
        <div className="data-card" style={{ padding: '0' }}>
            <div className="data-card-title">
                {title}
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {fields.map(field => (
                        <div key={field.key} className="flex flex-col gap-1">
                            <label className="text-xs font-medium text-muted uppercase tracking-wider">
                                {field.label}
                            </label>
                            {field.type === 'select' ? (
                                <select
                                    value={formValues[field.key] || ''}
                                    onChange={(e) => handleChange(field.key, e.target.value)}
                                    disabled={!field.editable || isLoading || disabled}
                                    className="bg-white/5 border border-white/10 rounded px-3 py-2 text-sm focus:border-accent-primary outline-none transition-all disabled:opacity-50 appearance-none"
                                >
                                    <option value="" disabled className="bg-slate-900">Select {field.label}</option>
                                    {field.options?.map(opt => (
                                        <option key={opt.value} value={opt.value} className="bg-slate-900">
                                            {opt.label}
                                        </option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    type={field.type || 'text'}
                                    value={formValues[field.key] || ''}
                                    onChange={(e) => handleChange(field.key, e.target.value)}
                                    disabled={!field.editable || isLoading || disabled}
                                    className="bg-white/5 border border-white/10 rounded px-3 py-2 text-sm focus:border-accent-primary outline-none transition-all disabled:opacity-50"
                                />
                            )}
                        </div>
                    ))}
                </div>
                <div className="pt-2 flex justify-end">
                    <Button
                        type="submit"
                        variant="primary"
                        size="sm"
                        isLoading={isLoading}
                        disabled={isLoading || disabled}
                    >
                        Confirm & Submit
                    </Button>
                </div>
            </form>
        </div>
    );
};
