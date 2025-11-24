import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, Heading, Flex, Link } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import TopicExplorer from './components/TopicExplorer';

function App() {
  return (
    <Box>
      <Flex as="nav" bg="gray.900" p={4} color="white" justify="space-between">
        <Heading size="md">Indian Tech News Monitor</Heading>
        <Flex>
          <Link as={RouterLink} to="/" p={2}>Dashboard</Link>
          <Link as={RouterLink} to="/explore" p={2}>Topic Explorer</Link>
        </Flex>
      </Flex>
      <Container maxW="container.xl" mt={8}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/explore" element={<TopicExplorer />} />
          <Route path="/explore/:topicId" element={<TopicExplorer />} />
        </Routes>
      </Container>
    </Box>
  );
}
export default App;
