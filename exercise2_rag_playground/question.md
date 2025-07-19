# Exercise 1: RAG Playground

You will be working with three distinct types of documents: a PDF file, a confluence link, and a link to a Google Document. For each type, utilize the appropriate document loaders to access and extract the content. Once loaded, the data from these documents should be segmented into manageable chunks suitable for database insertion.

Proceed to integrate these data chunks into the ChromaDB. Ensure the data is formatted correctly to comply with the database schema and optimize retrieval efficiency. If you are considering expanding the scope of this project beyond local storage solutions, Pinecone offers a scalable vector database option that can significantly enhance data retrieval capabilities. This could be particularly beneficial for complex query handling and large-scale data sets.

After the data insertion, formulate specific queries that you aim to run against the inserted documents. These queries should be designed to test the retrieval capabilities of your database setup and should align with the key information and insights you seek to extract from the stored documents.

Documents:
Confluence Link: Code of Conduct
Google Doc Link: Detailed Nomination Guidelines
PDF Link: Anti-Harassment Policy
