import React from 'react';

export interface DataColumn {
    header: string;
    key: string;
}

export interface DataCardProps {
    data: any[] | { columns: DataColumn[], rows: any[] };
    title?: string;
}

export const DataCard: React.FC<DataCardProps> = ({ data, title }) => {
    if (!data) return null;

    let rows: any[] = [];
    let columns: any[] = [];

    if (Array.isArray(data)) {
        if (data.length === 0) return null;
        rows = data;
        // Legacy: Extract keys from first object
        columns = Object.keys(data[0])
            .filter(key => !key.startsWith('__'))
            .map(key => ({
                header: key.replace(/_/g, ' ').toUpperCase(),
                key: key
            }));
    } else if (data.columns && data.rows) {
        rows = data.rows;
        columns = data.columns;
    } else {
        return null;
    }

    if (rows.length === 0) return null;

    return (
        <div className="data-card">
            {title && <div className="data-card-title">{title}</div>}
            <div className="data-card-table-wrapper">
                <table className="data-card-table" id="gen-ui-table">
                    <thead>
                        <tr>
                            {columns.map((col, idx) => (
                                <th key={col.key || idx}>{col.header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, i) => (
                            <tr key={i}>
                                {columns.map((col, idx) => {
                                    const val = row[col.key];
                                    let displayVal = '';

                                    if (val === null || val === undefined) {
                                        displayVal = '';
                                    } else if (typeof val === 'object') {
                                        // ServiceNow and CRM often return { display_value: '...' } or { text: '...' }
                                        displayVal = val.display_value || val.text || JSON.stringify(val);
                                    } else {
                                        displayVal = String(val);
                                    }

                                    return (
                                        <td key={col.key || idx}>
                                            {displayVal}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DataCard;
