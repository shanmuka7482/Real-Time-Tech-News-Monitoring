import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Heading,
  Select,
  Spinner,
  Alert,
  AlertIcon,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Text,
  Tag,
  HStack,
} from '@chakra-ui/react';
import ReactPlayer from 'react-player/youtube';
import * as api from '../api';

function TopicExplorer() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(topicId || '');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch the list of all topics for the dropdown
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const res = await api.getTopics();
        setTopics(res.data);
      } catch (err) {
        console.error("Failed to fetch topics list", err);
      }
    };
    fetchTopics();
  }, []);

  // Fetch documents when a topic is selected
  useEffect(() => {
    if (selectedTopic) {
      const fetchDocuments = async () => {
        setLoading(true);
        setError(null);
        try {
          const res = await api.getDocumentsForTopic(selectedTopic);
          setDocuments(res.data);
        } catch (err) {
          setError(`Failed to fetch documents for topic ${selectedTopic}.`);
          console.error(err);
        } finally {
          setLoading(false);
        }
      };
      fetchDocuments();
    }
  }, [selectedTopic]);

  const handleTopicChange = (event) => {
    const newTopicId = event.target.value;
    setSelectedTopic(newTopicId);
    navigate(`/explore/${newTopicId}`);
  };

  const currentTopic = topics.find(t => t.id === parseInt(selectedTopic));

  return (
    <Box>
      <Heading mb={4}>Topic Explorer</Heading>
      
      <Select 
        placeholder="Select a topic to explore" 
        onChange={handleTopicChange}
        value={selectedTopic}
        mb={6}
      >
        {topics.map(topic => (
          <option key={topic.id} value={topic.id}>
            {topic.name} ({topic.count} docs)
          </option>
        ))}
      </Select>

      {loading && <Spinner size="xl" />}
      {error && <Alert status="error"><AlertIcon />{error}</Alert>}

      {selectedTopic && !loading && (
        <Box>
          {currentTopic && (
            <Box mb={6}>
              <Heading size="lg">{currentTopic.name}</Heading>
              <HStack spacing={2} mt={2}>
                {currentTopic.keywords.split(', ').map(keyword => (
                  <Tag key={keyword} size="md" variant="solid" colorScheme="teal">
                    {keyword}
                  </Tag>
                ))}
              </HStack>
            </Box>
          )}

          <Accordion allowMultiple>
            {documents.map(doc => (
              <AccordionItem key={doc.id}>
                <h2>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      {doc.title}
                      <Tag size="sm" colorScheme={doc.source_type === 'video' ? 'red' : 'blue'} ml={3}>
                        {doc.source_type}
                      </Tag>
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  {doc.source_type === 'video' ? (
                    <Box sx={{ aspectRatio: '16/9', maxHeight: '500px' }}>
                      <ReactPlayer url={doc.url} width="100%" height="100%" controls />
                    </Box>
                  ) : (
                    <Text whiteSpace="pre-wrap">{doc.full_content}</Text>
                  )}
                </AccordionPanel>
              </AccordionItem>
            ))}
          </Accordion>
        </Box>
      )}
    </Box>
  );
}

export default TopicExplorer;
