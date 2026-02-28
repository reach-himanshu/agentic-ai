import React, { useState } from 'react';
import { Button, CheckIcon, XIcon, EditIcon } from './ui';

// TypeScript interfaces for ConfirmationCard data
export interface ConfirmationField {
    key: string;
    label: string;
    value: string;
    newValue?: string;        // If different from current value
    editable?: boolean;
    type?: 'text' | 'select';
    options?: string[];       // For select type
}

export interface ConfirmationCardData {
    title: string;
    description?: string;
    fields: ConfirmationField[];
    confirmLabel?: string;
    cancelLabel?: string;
    showEditButton?: boolean;
}

interface ConfirmationCardProps {
    data: ConfirmationCardData;
    onConfirm: (values: Record<string, string>) => void;
    onCancel: () => void;
    onEdit?: () => void;
}

export const ConfirmationCard: React.FC<ConfirmationCardProps> = ({
    data,
    onConfirm,
    onCancel,
    onEdit,
}) => {
    const {
        title,
        description,
        fields,
        confirmLabel = 'Confirm',
        cancelLabel = 'Cancel',
        showEditButton = false,
    } = data;

    // Track editable field values
    const [editableValues, setEditableValues] = useState<Record<string, string>>(() => {
        const initial: Record<string, string> = {};
        fields.forEach(field => {
            if (field.editable) {
                initial[field.key] = field.newValue || field.value;
            }
        });
        return initial;
    });

    const handleFieldChange = (key: string, value: string) => {
        setEditableValues(prev => ({ ...prev, [key]: value }));
    };

    const handleConfirm = () => {
        // Collect all field values
        const values: Record<string, string> = {};
        fields.forEach(field => {
            if (field.editable) {
                values[field.key] = editableValues[field.key];
            } else {
                values[field.key] = field.newValue || field.value;
            }
        });
        onConfirm(values);
    };

    return (
        <div className="confirmation-card">
            {/* Header */}
            <div className="confirmation-card-header">
                <div className="flex items-center gap-2">
                    <CheckIcon size={18} />
                    <h3>{title}</h3>
                </div>
                {description && (
                    <p style={{
                        marginTop: 'var(--spacing-2)',
                        fontSize: 'var(--font-size-sm)',
                        opacity: 0.9,
                    }}>
                        {description}
                    </p>
                )}
            </div>

            {/* Body - Data Fields */}
            <div className="confirmation-card-body">
                {fields.map((field) => (
                    <div key={field.key} className="data-row">
                        <span className="data-label">{field.label}</span>
                        {field.editable ? (
                            field.type === 'select' && field.options ? (
                                <select
                                    className="input"
                                    style={{
                                        width: 'auto',
                                        minWidth: '150px',
                                        padding: 'var(--spacing-2) var(--spacing-3)',
                                    }}
                                    value={editableValues[field.key]}
                                    onChange={(e) => handleFieldChange(field.key, e.target.value)}
                                >
                                    {field.options.map(opt => (
                                        <option key={opt} value={opt}>{opt}</option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    className="input"
                                    style={{
                                        width: 'auto',
                                        minWidth: '150px',
                                        padding: 'var(--spacing-2) var(--spacing-3)',
                                    }}
                                    value={editableValues[field.key]}
                                    onChange={(e) => handleFieldChange(field.key, e.target.value)}
                                />
                            )
                        ) : (
                            <span className={field.newValue ? 'data-value' : 'data-value'}>
                                {field.newValue ? (
                                    <span className="flex items-center gap-2">
                                        <span style={{ textDecoration: 'line-through', opacity: 0.5 }}>
                                            {field.value}
                                        </span>
                                        <span style={{ color: 'var(--color-accent-primary)' }}>→</span>
                                        <span className="data-value-changed">{field.newValue}</span>
                                    </span>
                                ) : (
                                    field.value
                                )}
                            </span>
                        )}
                    </div>
                ))}
            </div>

            {/* Footer - Actions */}
            <div className="confirmation-card-footer">
                <Button variant="secondary" onClick={onCancel}>
                    <XIcon size={16} />
                    {cancelLabel}
                </Button>
                {showEditButton && onEdit && (
                    <Button variant="secondary" onClick={onEdit}>
                        <EditIcon size={16} />
                        Edit
                    </Button>
                )}
                <Button variant="primary" onClick={handleConfirm}>
                    <CheckIcon size={16} />
                    {confirmLabel}
                </Button>
            </div>
        </div>
    );
};

export default ConfirmationCard;
