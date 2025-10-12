import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import toast from 'react-hot-toast';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: calc(100vh - 6rem);
  gap: 1rem;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
`;

const Title = styled.h1`
  font-size: 1.75rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.025em;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.75rem;
`;

const Button = styled.button`
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;

  ${props => props.primary && `
    background: #3b82f6;
    color: white;
    &:hover { background: #2563eb; }
    &:disabled {
      background: #cbd5e1;
      cursor: not-allowed;
    }
  `}

  ${props => props.secondary && `
    background: #f1f5f9;
    color: #475569;
    &:hover { background: #e2e8f0; }
  `}

  ${props => props.danger && `
    background: #ef4444;
    color: white;
    &:hover { background: #dc2626; }
  `}
`;

const ContentContainer = styled.div`
  display: flex;
  gap: 1rem;
  flex: 1;
  min-height: 0;
`;

const EditorSection = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
`;

const EditorHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
`;

const EditorTitle = styled.div`
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const VersionBadge = styled.span`
  background: #3b82f6;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
`;

const EditorWrapper = styled.div`
  flex: 1;
  position: relative;
  overflow: auto;
`;

const CodeEditor = styled.textarea`
  width: 100%;
  height: 100%;
  padding: 1rem;
  border: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  resize: none;
  outline: none;
  background: #ffffff;
  color: #0f172a;
  tab-size: 2;

  &:focus {
    background: #fef cefb;
  }
`;

const VersionPanel = styled.div`
  width: 300px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const VersionPanelHeader = styled.div`
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
`;

const VersionPanelTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
`;

const VersionList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
`;

const VersionItem = styled.div`
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;

  ${props => props.active && `
    background: #eff6ff;
    border-color: #3b82f6;
  `}

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }
`;

const VersionNumber = styled.div`
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ActiveLabel = styled.span`
  background: #10b981;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
`;

const VersionMeta = styled.div`
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.25rem;
`;

const VersionDescription = styled.div`
  font-size: 0.75rem;
  color: #475569;
  font-style: ${props => props.empty ? 'italic' : 'normal'};
`;

const ValidationMessage = styled.div`
  padding: 0.75rem 1rem;
  margin: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;

  ${props => props.type === 'error' && `
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
  `}

  ${props => props.type === 'warning' && `
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
  `}

  ${props => props.type === 'success' && `
    background: #dcfce7;
    color: #166534;
    border: 1px solid #bbf7d0;
  `}
`;

const ValidationList = styled.ul`
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
`;

function DSSEditor() {
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [versions, setVersions] = useState([]);
  const [activeVersionId, setActiveVersionId] = useState(null);
  const [currentVersionNumber, setCurrentVersionNumber] = useState(0);
  const [isDirty, setIsDirty] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load current DSS file and versions
  useEffect(() => {
    loadCurrentDSS();
    loadVersions();
  }, []);

  const loadCurrentDSS = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/dss/current');
      const data = await response.json();
      setContent(data.content);
      setOriginalContent(data.content);
      setActiveVersionId(data.version_id);
      setCurrentVersionNumber(data.version_number);
      setIsDirty(false);
    } catch (error) {
      console.error('Error loading DSS file:', error);
      toast.error('Failed to load DSS file');
    } finally {
      setIsLoading(false);
    }
  };

  const loadVersions = async () => {
    try {
      const response = await fetch('/api/dss/versions');
      const data = await response.json();
      setVersions(data.versions || []);
    } catch (error) {
      console.error('Error loading versions:', error);
    }
  };

  const handleContentChange = (e) => {
    setContent(e.target.value);
    setIsDirty(e.target.value !== originalContent);
    setValidationResult(null);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const description = prompt('Enter a description for this version (optional):');

      const response = await fetch('/api/dss/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          description: description || '',
          created_by: 'user'
        })
      });

      const result = await response.json();

      if (result.success) {
        toast.success('DSS file saved successfully!');
        setOriginalContent(content);
        setIsDirty(false);
        setValidationResult(null);
        await loadVersions();
        await loadCurrentDSS();
      } else {
        setValidationResult(result);
        toast.error('Failed to save: ' + result.message);
      }
    } catch (error) {
      console.error('Error saving DSS file:', error);
      toast.error('Failed to save DSS file');
    } finally {
      setIsSaving(false);
    }
  };

  const handleVersionClick = async (version) => {
    if (isDirty) {
      const confirm = window.confirm('You have unsaved changes. Do you want to discard them?');
      if (!confirm) return;
    }

    try {
      const response = await fetch(`/api/dss/versions/${version.id}`);
      const data = await response.json();
      setContent(data.content);
      setOriginalContent(data.content);
      setIsDirty(false);
      setValidationResult(null);
    } catch (error) {
      console.error('Error loading version:', error);
      toast.error('Failed to load version');
    }
  };

  const handleActivateVersion = async (versionId, versionNumber) => {
    const confirm = window.confirm(`Are you sure you want to activate version ${versionNumber}? This will reload the simulation with this version.`);
    if (!confirm) return;

    try {
      const response = await fetch(`/api/dss/activate/${versionId}`, {
        method: 'POST'
      });
      const result = await response.json();

      if (result.success) {
        toast.success(`Version ${versionNumber} activated!`);
        await loadVersions();
        await loadCurrentDSS();
      } else {
        toast.error('Failed to activate version');
      }
    } catch (error) {
      console.error('Error activating version:', error);
      toast.error('Failed to activate version');
    }
  };

  const handleReset = () => {
    if (isDirty) {
      const confirm = window.confirm('Are you sure you want to discard all changes?');
      if (!confirm) return;
    }

    setContent(originalContent);
    setIsDirty(false);
    setValidationResult(null);
  };

  if (isLoading) {
    return (
      <PageContainer>
        <Header>
          <Title>DSS File Editor</Title>
        </Header>
        <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <Header>
        <Title>DSS File Editor</Title>
        <ActionButtons>
          <Button secondary onClick={handleReset} disabled={!isDirty}>
            Reset
          </Button>
          <Button primary onClick={handleSave} disabled={!isDirty || isSaving}>
            {isSaving ? 'Saving...' : 'Save Version'}
          </Button>
        </ActionButtons>
      </Header>

      {validationResult && (
        <ValidationMessage type={validationResult.valid ? 'success' : 'error'}>
          <strong>{validationResult.message}</strong>
          {validationResult.errors && validationResult.errors.length > 0 && (
            <ValidationList>
              {validationResult.errors.map((error, i) => (
                <li key={i}>{error}</li>
              ))}
            </ValidationList>
          )}
          {validationResult.warnings && validationResult.warnings.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <strong>Warnings:</strong>
              <ValidationList>
                {validationResult.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ValidationList>
            </div>
          )}
        </ValidationMessage>
      )}

      <ContentContainer>
        <EditorSection>
          <EditorHeader>
            <EditorTitle>
              Circuit File
              <VersionBadge>v{currentVersionNumber}</VersionBadge>
              {isDirty && <span style={{ color: '#f59e0b', fontSize: '0.875rem' }}>●  Unsaved</span>}
            </EditorTitle>
            <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
              {content ? content.split('\n').length : 0} lines
            </div>
          </EditorHeader>
          <EditorWrapper>
            <CodeEditor
              value={content}
              onChange={handleContentChange}
              spellCheck="false"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
            />
          </EditorWrapper>
        </EditorSection>

        <VersionPanel>
          <VersionPanelHeader>
            <VersionPanelTitle>Version History</VersionPanelTitle>
          </VersionPanelHeader>
          <VersionList>
            {versions.length === 0 ? (
              <div style={{ padding: '1rem', textAlign: 'center', color: '#64748b' }}>
                No versions yet
              </div>
            ) : (
              versions.map((version) => (
                <VersionItem
                  key={version.id}
                  active={version.is_active}
                  onClick={() => handleVersionClick(version)}
                >
                  <VersionNumber>
                    Version {version.version_number}
                    {version.is_active && <ActiveLabel>HEAD</ActiveLabel>}
                  </VersionNumber>
                  <VersionMeta>
                    {new Date(version.created_at).toLocaleString()}
                  </VersionMeta>
                  <VersionMeta>
                    By {version.created_by}
                  </VersionMeta>
                  <VersionDescription empty={!version.description}>
                    {version.description || 'No description'}
                  </VersionDescription>
                  {!version.is_active && (
                    <Button
                      secondary
                      style={{ marginTop: '0.5rem', width: '100%', fontSize: '0.75rem', padding: '0.375rem 0.5rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleActivateVersion(version.id, version.version_number);
                      }}
                    >
                      Activate
                    </Button>
                  )}
                </VersionItem>
              ))
            )}
          </VersionList>
        </VersionPanel>
      </ContentContainer>
    </PageContainer>
  );
}

export default DSSEditor;
