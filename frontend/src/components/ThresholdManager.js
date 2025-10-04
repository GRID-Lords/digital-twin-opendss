import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiEdit2, FiTrash2, FiPlus, FiSave, FiX, FiAlertTriangle } from 'react-icons/fi';
import axios from 'axios';

const ManagerContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ControlsRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const AddButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;

  &:hover {
    background: #2563eb;
  }

  svg {
    font-size: 1rem;
  }
`;

const InitButton = styled(AddButton)`
  background: #10b981;

  &:hover {
    background: #059669;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.875rem;
`;

const TableHeader = styled.thead`
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
`;

const TableHeaderCell = styled.th`
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;

  &:first-child {
    padding-left: 1.5rem;
  }

  &:last-child {
    padding-right: 1.5rem;
  }
`;

const TableBody = styled.tbody``;

const TableRow = styled.tr`
  border-bottom: 1px solid #e2e8f0;
  transition: background-color 0.2s ease;

  &:hover {
    background: #f8fafc;
  }

  &:last-child {
    border-bottom: none;
  }
`;

const TableCell = styled.td`
  padding: 0.875rem 1rem;
  color: #334155;

  &:first-child {
    padding-left: 1.5rem;
  }

  &:last-child {
    padding-right: 1.5rem;
  }
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const ActionButton = styled.button`
  padding: 0.375rem 0.625rem;
  border: 1px solid ${props => props.delete ? '#ef4444' : '#3b82f6'};
  background: ${props => props.delete ? '#fef2f2' : '#eff6ff'};
  color: ${props => props.delete ? '#dc2626' : '#2563eb'};
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  transition: all 0.2s;

  &:hover {
    background: ${props => props.delete ? '#fee2e2' : '#dbeafe'};
  }

  svg {
    font-size: 0.875rem;
  }
`;

const ActionsCell = styled(TableCell)`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const SeverityBadge = styled.span`
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  background: ${props => {
    if (props.severity === 'high') return '#fef2f2';
    if (props.severity === 'medium') return '#fffbeb';
    return '#f0fdf4';
  }};
  color: ${props => {
    if (props.severity === 'high') return '#dc2626';
    if (props.severity === 'medium') return '#f59e0b';
    return '#16a34a';
  }};
  border: 1px solid ${props => {
    if (props.severity === 'high') return '#fca5a5';
    if (props.severity === 'medium') return '#fde68a';
    return '#86efac';
  }};
`;

const StatusText = styled.span`
  color: ${props => props.enabled ? '#16a34a' : '#64748b'};
  font-weight: 500;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 2rem;
  color: #64748b;

  svg {
    font-size: 3rem;
    color: #cbd5e1;
    margin-bottom: 1rem;
  }

  p {
    margin: 0;
    font-size: 0.875rem;
  }
`;

const ThresholdManager = () => {
  const [thresholds, setThresholds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    fetchThresholds();
  }, []);

  const fetchThresholds = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/thresholds');
      setThresholds(response.data.thresholds || []);
    } catch (error) {
      console.error('Error fetching thresholds:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInitializeDefaults = async () => {
    try {
      await axios.post('/api/thresholds/initialize-defaults');
      fetchThresholds();
    } catch (error) {
      console.error('Error initializing defaults:', error);
    }
  };

  const handleEdit = (threshold) => {
    setEditingId(threshold.id);
    setEditForm({ ...threshold });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleSaveEdit = async () => {
    try {
      await axios.put(`/api/thresholds/${editingId}`, {
        threshold_min: editForm.threshold_min ? parseFloat(editForm.threshold_min) : null,
        threshold_max: editForm.threshold_max ? parseFloat(editForm.threshold_max) : null,
        severity: editForm.severity,
        enabled: editForm.enabled,
        description: editForm.description
      });
      setEditingId(null);
      setEditForm({});
      fetchThresholds();
    } catch (error) {
      console.error('Error saving threshold:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this threshold?')) {
      try {
        await axios.delete(`/api/thresholds/${id}`);
        fetchThresholds();
      } catch (error) {
        console.error('Error deleting threshold:', error);
      }
    }
  };

  const handleFieldChange = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return <div>Loading thresholds...</div>;
  }

  return (
    <ManagerContainer>
      {thresholds.length === 0 && (
        <ControlsRow>
          <InitButton onClick={handleInitializeDefaults}>
            <FiPlus />
            Initialize Default Thresholds
          </InitButton>
        </ControlsRow>
      )}

      {thresholds.length === 0 ? (
        <EmptyState>
          <FiAlertTriangle />
          <p>No thresholds configured. Click "Initialize Default Thresholds" to get started.</p>
        </EmptyState>
      ) : (
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Component</TableHeaderCell>
              <TableHeaderCell>Metric</TableHeaderCell>
              <TableHeaderCell>Min</TableHeaderCell>
              <TableHeaderCell>Max</TableHeaderCell>
              <TableHeaderCell>Unit</TableHeaderCell>
              <TableHeaderCell>Severity</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Actions</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {thresholds.map((threshold) => (
              <TableRow key={threshold.id}>
                {editingId === threshold.id ? (
                  <>
                    <TableCell>{threshold.component_name}</TableCell>
                    <TableCell>{threshold.metric_name}</TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.1"
                        value={editForm.threshold_min || ''}
                        onChange={(e) => handleFieldChange('threshold_min', e.target.value)}
                        placeholder="Min"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.1"
                        value={editForm.threshold_max || ''}
                        onChange={(e) => handleFieldChange('threshold_max', e.target.value)}
                        placeholder="Max"
                      />
                    </TableCell>
                    <TableCell>{threshold.metric_unit}</TableCell>
                    <TableCell>
                      <Select
                        value={editForm.severity}
                        onChange={(e) => handleFieldChange('severity', e.target.value)}
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Select
                        value={editForm.enabled}
                        onChange={(e) => handleFieldChange('enabled', e.target.value === 'true')}
                      >
                        <option value="true">Enabled</option>
                        <option value="false">Disabled</option>
                      </Select>
                    </TableCell>
                    <ActionsCell>
                      <ActionButton onClick={handleSaveEdit}>
                        <FiSave /> Save
                      </ActionButton>
                      <ActionButton onClick={handleCancelEdit} delete>
                        <FiX /> Cancel
                      </ActionButton>
                    </ActionsCell>
                  </>
                ) : (
                  <>
                    <TableCell>{threshold.component_name}</TableCell>
                    <TableCell>{threshold.metric_name}</TableCell>
                    <TableCell>{threshold.threshold_min !== null ? threshold.threshold_min : '-'}</TableCell>
                    <TableCell>{threshold.threshold_max !== null ? threshold.threshold_max : '-'}</TableCell>
                    <TableCell>{threshold.metric_unit || '-'}</TableCell>
                    <TableCell>
                      <SeverityBadge severity={threshold.severity}>{threshold.severity}</SeverityBadge>
                    </TableCell>
                    <TableCell>
                      <StatusText enabled={threshold.enabled}>
                        {threshold.enabled ? 'Enabled' : 'Disabled'}
                      </StatusText>
                    </TableCell>
                    <ActionsCell>
                      <ActionButton onClick={() => handleEdit(threshold)}>
                        <FiEdit2 /> Edit
                      </ActionButton>
                      <ActionButton onClick={() => handleDelete(threshold.id)} delete>
                        <FiTrash2 /> Delete
                      </ActionButton>
                    </ActionsCell>
                  </>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </ManagerContainer>
  );
};

export default ThresholdManager;
