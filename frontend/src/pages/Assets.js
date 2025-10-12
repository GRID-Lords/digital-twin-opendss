import React, { useState, useMemo } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { Search, ChevronDown, ChevronUp, Power, RotateCcw } from 'lucide-react';
import toast from 'react-hot-toast';

const Container = styled.div`
  display: flex;
  flex-direction: column;
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
  letter-spacing: -0.025em;
`;

const Stats = styled.div`
  display: flex;
  gap: 1.5rem;
  font-size: 0.875rem;
`;

const Stat = styled.div`
  color: #64748b;

  strong {
    color: #0f172a;
    font-weight: 600;
    margin-left: 0.25rem;
  }
`;

const Controls = styled.div`
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
`;

const SearchBox = styled.div`
  position: relative;
  flex: 1;
  max-width: 400px;
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #0f172a;
  background: white;
  transition: all 0.15s;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  &::placeholder {
    color: #94a3b8;
  }
`;

const SearchIcon = styled(Search)`
  position: absolute;
  left: 0.625rem;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #94a3b8;
`;

const Select = styled.select`
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #0f172a;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  transition: all 0.15s;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const TableCard = styled.div`
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow: hidden;
`;

const TableWrapper = styled.div`
  overflow-x: auto;
  overflow-y: visible;

  &::-webkit-scrollbar {
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #f1f5f9;
  }

  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
`;

const Table = styled.table`
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
  font-size: 0.8125rem;
`;

const Thead = styled.thead`
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
`;

const Th = styled.th`
  padding: 0.625rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: ${props => props.sortable ? 'pointer' : 'default'};
  user-select: none;
  white-space: nowrap;
  transition: color 0.15s;

  &:hover {
    ${props => props.sortable && `color: #0f172a;`}
  }
`;

const Tbody = styled.tbody``;

const Tr = styled.tr`
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.15s;

  &:hover {
    background: #f8fafc;
  }

  &:last-child {
    border-bottom: none;
  }
`;

const Td = styled.td`
  padding: 0.75rem;
  color: #0f172a;
  vertical-align: middle;
`;

const AssetName = styled.div`
  font-weight: 600;
  font-size: 0.8125rem;
  color: #0f172a;
  margin-bottom: 0.125rem;
`;

const AssetId = styled.div`
  font-size: 0.6875rem;
  color: #94a3b8;
`;

const StatusBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: capitalize;
  white-space: nowrap;

  ${props => {
    switch(props.status) {
      case 'operational':
      case 'healthy':
        return `background: #dcfce7; color: #166534;`;
      case 'warning':
        return `background: #fef3c7; color: #92400e;`;
      case 'fault':
        return `background: #fee2e2; color: #991b1b;`;
      case 'maintenance':
        return `background: #dbeafe; color: #1e40af;`;
      default:
        return `background: #f1f5f9; color: #64748b;`;
    }
  }}
`;

const StatusDot = styled.span`
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: currentColor;
`;

const HealthBar = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const HealthTrack = styled.div`
  flex: 1;
  height: 4px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
  max-width: 80px;
`;

const HealthFill = styled.div`
  height: 100%;
  background: ${props => {
    if (props.value >= 90) return '#10b981';
    if (props.value >= 70) return '#f59e0b';
    return '#ef4444';
  }};
  width: ${props => props.value}%;
  transition: width 0.3s ease;
`;

const HealthText = styled.span`
  font-weight: 600;
  font-size: 0.6875rem;
  min-width: 32px;
  color: ${props => {
    if (props.value >= 90) return '#166534';
    if (props.value >= 70) return '#92400e';
    return '#991b1b';
  }};
`;

const Btn = styled.button`
  padding: 0.25rem 0.625rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: white;
  color: #0f172a;

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }

  ${props => props.variant === 'danger' && `
    background: #fee2e2;
    color: #991b1b;
    border-color: #fecaca;
    &:hover { background: #fecaca; }
  `}

  ${props => props.variant === 'primary' && `
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
    &:hover { background: #2563eb; }
  `}
`;

const BtnGroup = styled.div`
  display: flex;
  gap: 0.25rem;
`;

const ExpandIcon = styled.button`
  padding: 0.125rem;
  border: none;
  background: none;
  cursor: pointer;
  color: #64748b;
  display: flex;
  align-items: center;

  &:hover {
    color: #0f172a;
  }
`;

const ExpandedRow = styled.tr`
  background: #f8fafc;
`;

const ExpandedContent = styled.td`
  padding: 1rem 0.75rem;
  border-top: 1px solid #e2e8f0;
`;

const DetailsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
`;

const Detail = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
`;

const DetailLabel = styled.span`
  font-size: 0.6875rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  font-weight: 500;
`;

const DetailValue = styled.span`
  font-size: 0.8125rem;
  color: #0f172a;
  font-weight: 600;
`;

const Footer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
`;

const FooterInfo = styled.div`
  font-size: 0.8125rem;
  color: #64748b;
`;

const PageControls = styled.div`
  display: flex;
  gap: 0.25rem;
`;

const PageBtn = styled.button`
  padding: 0.375rem 0.625rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
  cursor: pointer;
  background: white;
  color: #0f172a;
  transition: all 0.15s;
  min-width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover:not(:disabled) {
    background: #f8fafc;
    border-color: #cbd5e1;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  ${props => props.active && `
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
  `}
`;

const EmptyState = styled.div`
  padding: 3rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.875rem;
`;

const Assets = () => {
  const { assets, controlAsset } = useDigitalTwin();

  // Convert assets object to array
  const assetsArray = useMemo(() => {
    if (!assets) return [];

    // If already array
    if (Array.isArray(assets)) return assets;

    // If it's the backend response with assets key
    if (assets.assets && Array.isArray(assets.assets)) return assets.assets;

    // If it's an object, convert to array
    return Object.entries(assets).map(([id, asset]) => ({
      id: asset.id || id,
      name: asset.name || id,
      type: asset.type || asset.asset_type || 'Unknown',
      status: asset.status || 'operational',
      health: asset.health || asset.health_score || 100,
      parameters: asset.parameters || {},
      ...asset
    }));
  }, [assets]);

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortCol, setSortCol] = useState('name');
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState(new Set());
  const pageSize = 10;

  const types = useMemo(() =>
    ['all', ...new Set(assetsArray.map(a => a.type))],
    [assetsArray]
  );

  const filtered = useMemo(() => {
    return assetsArray.filter(a => {
      const matchSearch = (a.name?.toLowerCase().includes(search.toLowerCase()) ||
                          a.id?.toLowerCase().includes(search.toLowerCase()));
      const matchType = typeFilter === 'all' || a.type === typeFilter;
      const matchStatus = statusFilter === 'all' || a.status === statusFilter;
      return matchSearch && matchType && matchStatus;
    });
  }, [assetsArray, search, typeFilter, statusFilter]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let av, bv;
      if (sortCol === 'name') { av = a.name; bv = b.name; }
      else if (sortCol === 'type') { av = a.type; bv = b.type; }
      else if (sortCol === 'status') { av = a.status; bv = b.status; }
      else if (sortCol === 'health') { av = a.health; bv = b.health; }
      else if (sortCol === 'voltage') {
        av = parseFloat(a.parameters?.voltage || 0);
        bv = parseFloat(b.parameters?.voltage || 0);
      }
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filtered, sortCol, sortDir]);

  const paginated = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, page, pageSize]);

  const totalPages = Math.ceil(sorted.length / pageSize);

  const getPageNumbers = () => {
    const pages = [];
    const delta = 2; // Show 2 pages before and after current

    if (totalPages <= 7) {
      // Show all pages if 7 or fewer
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      // Calculate range around current page
      let start = Math.max(2, page - delta);
      let end = Math.min(totalPages - 1, page + delta);

      // Adjust range if near start or end
      if (page <= delta + 2) {
        end = Math.min(totalPages - 1, 5);
      }
      if (page >= totalPages - delta - 1) {
        start = Math.max(2, totalPages - 4);
      }

      // Add ellipsis if gap after first page
      if (start > 2) {
        pages.push('...');
      }

      // Add pages in range
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      // Add ellipsis if gap before last page
      if (end < totalPages - 1) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  };

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(col);
      setSortDir('asc');
    }
  };

  const toggleExpand = (id) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpanded(newExpanded);
  };

  const handleControl = async (id, action) => {
    try {
      await controlAsset(id, action);
      toast.success(`${action} completed`);
    } catch (error) {
      toast.error(`Failed to ${action}`);
    }
  };

  const getActions = (asset) => {
    const btns = [];
    if (asset.type === 'CircuitBreaker' || asset.type === 'circuit_breaker') {
      if (asset.status === 'operational') {
        btns.push(
          <Btn key="open" variant="danger" onClick={() => handleControl(asset.id, 'open')}>
            <Power size={12} /> Open
          </Btn>
        );
      } else {
        btns.push(
          <Btn key="close" variant="primary" onClick={() => handleControl(asset.id, 'close')}>
            <Power size={12} /> Close
          </Btn>
        );
      }
    }
    if (asset.status === 'fault') {
      btns.push(
        <Btn key="reset" onClick={() => handleControl(asset.id, 'reset')}>
          <RotateCcw size={12} /> Reset
        </Btn>
      );
    }
    return btns;
  };

  const statusCounts = useMemo(() => {
    return assetsArray.reduce((acc, a) => {
      acc[a.status] = (acc[a.status] || 0) + 1;
      return acc;
    }, {});
  }, [assetsArray]);

  return (
    <Container>
      <Header>
        <Title>Assets</Title>
        <Stats>
          <Stat>Total <strong>{assetsArray.length}</strong></Stat>
          <Stat>Operational <strong>{statusCounts.operational || 0}</strong></Stat>
          <Stat>Warning <strong>{statusCounts.warning || 0}</strong></Stat>
          <Stat>Fault <strong>{statusCounts.fault || 0}</strong></Stat>
        </Stats>
      </Header>

      <Controls>
        <SearchBox>
          <SearchIcon />
          <SearchInput
            placeholder="Search assets..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </SearchBox>
        <Select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}>
          {types.map(t => (
            <option key={t} value={t}>{t === 'all' ? 'All Types' : t}</option>
          ))}
        </Select>
        <Select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="all">All Status</option>
          <option value="operational">Operational</option>
          <option value="warning">Warning</option>
          <option value="fault">Fault</option>
        </Select>
      </Controls>

      <TableCard>
        <TableWrapper>
          <Table>
            <Thead>
              <tr>
                <Th style={{ width: '32px' }}></Th>
                <Th sortable onClick={() => handleSort('name')}>
                  Name {sortCol === 'name' && (sortDir === 'asc' ? '↑' : '↓')}
                </Th>
                <Th sortable onClick={() => handleSort('type')}>
                  Type {sortCol === 'type' && (sortDir === 'asc' ? '↑' : '↓')}
                </Th>
                <Th sortable onClick={() => handleSort('status')}>
                  Status {sortCol === 'status' && (sortDir === 'asc' ? '↑' : '↓')}
                </Th>
                <Th sortable onClick={() => handleSort('voltage')}>
                  Voltage {sortCol === 'voltage' && (sortDir === 'asc' ? '↑' : '↓')}
                </Th>
                <Th sortable onClick={() => handleSort('health')}>
                  Health {sortCol === 'health' && (sortDir === 'asc' ? '↑' : '↓')}
                </Th>
                <Th>Temp</Th>
                <Th>Actions</Th>
              </tr>
            </Thead>
            <Tbody>
              {paginated.length === 0 ? (
                <tr>
                  <Td colSpan="8">
                    <EmptyState>No assets found</EmptyState>
                  </Td>
                </tr>
              ) : (
                paginated.map((asset) => (
                  <React.Fragment key={asset.id}>
                    <Tr>
                      <Td>
                        <ExpandIcon onClick={() => toggleExpand(asset.id)}>
                          {expanded.has(asset.id) ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </ExpandIcon>
                      </Td>
                      <Td>
                        <AssetName>{asset.name}</AssetName>
                        <AssetId>{asset.id}</AssetId>
                      </Td>
                      <Td>{asset.type}</Td>
                      <Td>
                        <StatusBadge status={asset.status}>
                          <StatusDot />
                          {asset.status}
                        </StatusBadge>
                      </Td>
                      <Td>{asset.parameters?.voltage || 'N/A'}</Td>
                      <Td>
                        <HealthBar>
                          <HealthTrack>
                            <HealthFill value={asset.health} />
                          </HealthTrack>
                          <HealthText value={asset.health}>{asset.health}%</HealthText>
                        </HealthBar>
                      </Td>
                      <Td>{asset.parameters?.temperature || 'N/A'}</Td>
                      <Td>
                        <BtnGroup>
                          {getActions(asset)}
                        </BtnGroup>
                      </Td>
                    </Tr>
                    {expanded.has(asset.id) && (
                      <ExpandedRow>
                        <ExpandedContent colSpan="8">
                          <DetailsGrid>
                            <Detail>
                              <DetailLabel>Location</DetailLabel>
                              <DetailValue>{asset.parameters?.location || 'N/A'}</DetailValue>
                            </Detail>
                            <Detail>
                              <DetailLabel>Rating</DetailLabel>
                              <DetailValue>{asset.parameters?.rating || 'N/A'}</DetailValue>
                            </Detail>
                            {asset.parameters?.operations && (
                              <Detail>
                                <DetailLabel>Operations</DetailLabel>
                                <DetailValue>{asset.parameters.operations.toLocaleString()}</DetailValue>
                              </Detail>
                            )}
                            {asset.parameters?.oil_level && (
                              <Detail>
                                <DetailLabel>Oil Level</DetailLabel>
                                <DetailValue>{asset.parameters.oil_level}</DetailValue>
                              </Detail>
                            )}
                            {asset.parameters?.sf6_pressure && (
                              <Detail>
                                <DetailLabel>SF6 Pressure</DetailLabel>
                                <DetailValue>{asset.parameters.sf6_pressure}</DetailValue>
                              </Detail>
                            )}
                            {asset.parameters?.reliability && (
                              <Detail>
                                <DetailLabel>Reliability</DetailLabel>
                                <DetailValue>{asset.parameters.reliability}</DetailValue>
                              </Detail>
                            )}
                          </DetailsGrid>
                        </ExpandedContent>
                      </ExpandedRow>
                    )}
                  </React.Fragment>
                ))
              )}
            </Tbody>
          </Table>
        </TableWrapper>

        {totalPages > 1 && (
          <Footer>
            <FooterInfo>
              Showing {((page - 1) * pageSize) + 1}–{Math.min(page * pageSize, sorted.length)} of {sorted.length}
            </FooterInfo>
            <PageControls>
              <PageBtn onClick={() => setPage(1)} disabled={page === 1} title="First page">
                «
              </PageBtn>
              <PageBtn onClick={() => setPage(p => p - 1)} disabled={page === 1} title="Previous page">
                ‹
              </PageBtn>
              {getPageNumbers().map((pageNum, idx) => (
                pageNum === '...' ? (
                  <span key={`ellipsis-${idx}`} style={{ padding: '0.375rem 0.5rem', color: '#94a3b8' }}>
                    …
                  </span>
                ) : (
                  <PageBtn key={pageNum} active={page === pageNum} onClick={() => setPage(pageNum)}>
                    {pageNum}
                  </PageBtn>
                )
              ))}
              <PageBtn onClick={() => setPage(p => p + 1)} disabled={page === totalPages} title="Next page">
                ›
              </PageBtn>
              <PageBtn onClick={() => setPage(totalPages)} disabled={page === totalPages} title="Last page">
                »
              </PageBtn>
            </PageControls>
          </Footer>
        )}
      </TableCard>
    </Container>
  );
};

export default Assets;
