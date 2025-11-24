import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Spinner,
  Alert,
  AlertIcon,
  Button,
  useToast,
} from '@chakra-ui/react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';
import * as api from '../api';

function Dashboard() {
  const [topics, setTopics] = useState([]);
  const [temporalData, setTemporalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const topicsRes = await api.getTopics();
        const temporalRes = await api.getTemporalData();
        setTopics(topicsRes.data);
        setTemporalData(temporalRes.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch data. Is the backend running?');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleTrainClick = async () => {
    toast({
      title: 'Training started',
      description: 'The initial model training has been triggered. This may take a few minutes.',
      status: 'info',
      duration: 9000,
      isClosable: true,
    });
    try {
      await api.triggerInitialTrain();
    } catch (err) {
      toast({
        title: 'Training failed',
        description: 'Could not start the training process.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  if (loading) {
    return <Spinner size="xl" />;
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        {error}
        <Button onClick={handleTrainClick} ml={4}>Trigger Initial Training</Button>
      </Alert>
    );
  }

  const totalDocuments = Array.isArray(topics) ? topics.reduce((acc, topic) => acc + topic.count, 0) : 0;
  const uniqueTopics = Array.isArray(topics) ? topics.length : 0;

  return (
    <Box>
      <Heading mb={6}>Dashboard</Heading>
      
      <StatGroup mb={8}>
        <Stat>
          <StatLabel>Total Documents Analyzed</StatLabel>
          <StatNumber>{totalDocuments}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Discovered Topics</StatLabel>
          <StatNumber>{uniqueTopics}</StatNumber>
          <StatHelpText>Excluding outliers</StatHelpText>
        </Stat>
      </StatGroup>

      <Box mb={8}>
        <Heading size="lg" mb={4}>Topic Frequency Over Time</Heading>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={temporalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            {Array.isArray(topics) && topics.slice(0, 5).map((topic, index) => (
              <Line key={topic.id} type="monotone" dataKey={topic.name} stroke={`#${Math.floor(Math.random()*16777215).toString(16)}`} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </Box>

      <Heading size="lg" mb={4}>Top Topics</Heading>
      <TableContainer>
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Topic Name</Th>
              <Th>Keywords</Th>
              <Th isNumeric>Document Count</Th>
            </Tr>
          </Thead>
          <Tbody>
            {Array.isArray(topics) && topics.map((topic) => (
              <Tr key={topic.id} _hover={{ bg: 'gray.700', cursor: 'pointer' }} onClick={() => navigate(`/explore/${topic.id}`)}>
                <Td>{topic.name}</Td>
                <Td>{topic.keywords}</Td>
                <Td isNumeric>{topic.count}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default Dashboard;
