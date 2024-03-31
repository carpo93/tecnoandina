import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, Table, Pagination, Spinner, Form, Row, Col, Button, Toast, Badge } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

const AlertsList = () => {
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10); // Número de alertas por página
  const [sortColumn, setSortColumn] = useState(null);
  const [sortOrder, setSortOrder] = useState('asc');
  const [versionFilter, setVersionFilter] = useState('1');
  const [typeFilter, setTypeFilter] = useState(null);
  const [sendedFilter, setSendedFilter] = useState(null);
  const [procesarBtnDisabled, setProcesarBtnDisabled] = useState(true);
  const [enviarBtnDisabled, setEnviarBtnDisabled] = useState(true);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  useEffect(() => {
    obtenerAlertas();
  }, [versionFilter, typeFilter, sendedFilter]);

  const obtenerAlertas = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8083/challenge/search', {
        version: versionFilter !== 'todos' ? parseInt(versionFilter) : null,
        type: typeFilter !== 'todos' ? typeFilter : null,
        sended: sendedFilter !== 'todos' ? (sendedFilter === 'si' ? true : (sendedFilter === 'no' ? false : null)) : null
      });
      setAlertas(response.data);
    } catch (error) {
      console.error('Error al obtener alertas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = columnName => {
    if (sortColumn === columnName) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnName);
      setSortOrder('asc');
    }
  };

  const sortedItems = alertas.sort((a, b) => {
    if (sortColumn && sortOrder) {
      const columnA = typeof a[sortColumn] === 'string' ? a[sortColumn].toLowerCase() : a[sortColumn];
      const columnB = typeof b[sortColumn] === 'string' ? b[sortColumn].toLowerCase() : b[sortColumn];

      if (columnA < columnB) {
        return sortOrder === 'asc' ? -1 : 1;
      }
      if (columnA > columnB) {
        return sortOrder === 'asc' ? 1 : -1;
      }
      return 0;
    }
    return 0;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = sortedItems.slice(indexOfFirstItem, indexOfLastItem);

  const procesarAlertas = async () => {
    try {
      const response = await axios.post('http://localhost:8083/challenge/process', {
        version: versionFilter !== 'todos' ? parseInt(versionFilter) : null,
        timeSearch: '30d'
      });
      setToastMessage('Las alertas de los últimos 30 días has sido procesadas con éxito');
      setShowToast(true);
    } catch (error) {
      console.error('Error al obtener alertas:', error);
    }
  };

  const enviarAlertas = async () => {
    try {
      const response = await axios.post('http://localhost:8083/challenge/send', {
        version: versionFilter !== 'todos' ? parseInt(versionFilter) : null,
        type: typeFilter !== 'todos' ? typeFilter : null
      });
      setToastMessage('Las alertas seleccionadas has sido enviadas con éxito');
      setShowToast(true);
    } catch (error) {
      console.error('Error al obtener alertas:', error);
    }
  };

  const aplicarFiltros = () => {
    obtenerAlertas();
  };

  useEffect(() => {
    // Validación para deshabilitar el botón de procesar alertas
    setProcesarBtnDisabled(versionFilter === 'todos');

    // Validación para deshabilitar el botón de enviar alertas
    setEnviarBtnDisabled(versionFilter === 'todos' || typeFilter === 'todos');
  }, [versionFilter, typeFilter]);

  const renderPaginationItems = () => {
    const totalPages = Math.ceil(sortedItems.length / itemsPerPage);
    const maxPagesToShow = 10;
    let startPage = Math.max(currentPage - Math.floor(maxPagesToShow / 2), 1);
    let endPage = Math.min(startPage + maxPagesToShow - 1, totalPages);

    if (totalPages <= maxPagesToShow) {
      startPage = 1;
      endPage = totalPages;
    } else if (currentPage <= Math.ceil(maxPagesToShow / 2)) {
      startPage = 1;
      endPage = maxPagesToShow;
    } else if (currentPage + Math.floor(maxPagesToShow / 2) >= totalPages) {
      startPage = totalPages - maxPagesToShow + 1;
      endPage = totalPages;
    }

    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <Pagination.Item key={i} active={i === currentPage} onClick={() => setCurrentPage(i)}>
          {i}
        </Pagination.Item>
      );
    }
    return pages;
  };

  return (
    <div>
      <div className="w-100 mb-4">
        <Card>
          <Card.Header>Selección de parámetros</Card.Header>
          <Card.Body>
            <Form className="w-50">
              <Row className="align-items-center">
                <Col>
                  <Form.Group controlId="versionFilter">
                    <Form.Label>Versión:</Form.Label>
                    <Form.Control as="select" value={versionFilter} onChange={e => setVersionFilter(e.target.value)}>
                      <option value="1">1</option>
                      <option value="2">2</option>
                    </Form.Control>
                  </Form.Group>
                </Col>
                <Col>
                  <Form.Group controlId="typeFilter">
                    <Form.Label>Tipos de Alerta:</Form.Label>
                    <Form.Control as="select" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
                      <option value="todos">Todas</option>
                      <option value="ALTA">ALTA</option>
                      <option value="MEDIA">MEDIA</option>
                      <option value="BAJA">BAJA</option>
                    </Form.Control>
                  </Form.Group>
                </Col>
                <Col>
                  <Form.Group controlId="sendedFilter">
                    <Form.Label>Enviado:</Form.Label>
                    <Form.Control as="select" value={sendedFilter} onChange={e => setSendedFilter(e.target.value)}>
                      <option value="todos">Todos</option>
                      <option value="si">Sí</option>
                      <option value="no">No</option>
                    </Form.Control>
                  </Form.Group>
                </Col>
              </Row>
              <Row>
                <Col>
                  <br></br>
                  <Button variant="primary" onClick={aplicarFiltros}>Actualizar</Button>
                </Col>
              </Row>
            </Form>
          </Card.Body>
        </Card>
      </div>
      <div className="w-100">
        <Card>
          <Card.Header>Listado de alertas</Card.Header>
          <Card.Body>
            {loading ? (
              <Spinner animation="border" role="status">
                <span className="sr-only">Cargando...</span>
              </Spinner>
            ) : (
              <div>
                <Table striped bordered hover className="table-sm">
                  <thead>
                    <tr>
                      <th onClick={() => handleSort('datetime')}>Fecha</th>
                      <th onClick={() => handleSort('value')}>Valor</th>
                      <th onClick={() => handleSort('version')}>Versión</th>
                      <th onClick={() => handleSort('type')}>Tipo</th>
                      <th onClick={() => handleSort('sended')}>Enviado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentItems.map(alerta => (
                      <tr key={alerta.id_alerta}>
                        <td>{alerta.datetime}</td>
                        <td><Badge bg="dark">{alerta.value}</Badge></td>
                        <td><Badge bg="primary">{alerta.version}</Badge></td>
                        <td><Badge bg="secondary">{alerta.type}</Badge></td>
                        <td>{alerta.sended ? 'Sí' : 'No'}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
                <Pagination className="d-flex justify-content-center">
                  {renderPaginationItems()}
                </Pagination>
              </div>
            )}
          </Card.Body>
          <Card.Footer>
            <Button variant="primary" onClick={procesarAlertas} disabled={procesarBtnDisabled}>
              Procesar Alertas
            </Button>{' '}
            <Button variant="success" onClick={enviarAlertas} disabled={enviarBtnDisabled}>
              Enviar Alertas
            </Button>
          </Card.Footer>
        </Card>
        <Toast show={showToast} onClose={() => setShowToast(false)} delay={5000} autohide>
          <Toast.Header>
            <strong className="mr-auto">Mensaje</strong>
          </Toast.Header>
          <Toast.Body>{toastMessage}</Toast.Body>
        </Toast>
      </div>
    </div>
  );
};

export default AlertsList;