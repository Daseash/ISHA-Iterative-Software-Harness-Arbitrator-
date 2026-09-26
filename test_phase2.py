from src.ingestion.parser import RepoParser
from src.tools.ast_mapper import ASTMapper
from src.rag.retriever import CodeRetriever
from src.rag.indexer import QdrantIndexer

parser = RepoParser()
chunks = parser.parse("tests/dummy_repo")
print(f"Parsed {len(chunks)} chunks")
assert len(chunks) > 0, "Parser returned no chunks!"

mapper = ASTMapper()
repo_map = mapper.build_map("tests/dummy_repo")
print("Repo Map:\n", repo_map)
assert "Calculator" in repo_map, "AST map missing Calculator class!"
assert "subtract" in repo_map, "AST map missing subtract method!"

idx = QdrantIndexer()
meta = idx.index(chunks)
print("Index:", meta)

retriever = CodeRetriever(chunks=chunks)
results = retriever.search("subtract method bug")
print(f"Found {len(results)} results for 'subtract method bug'")
assert len(results) > 0

print("\nPhase 2 PASSED - Ingestion + RAG working!")
