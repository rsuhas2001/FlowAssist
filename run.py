"""Start the local portfolio demo on http://127.0.0.1:8012."""
import os
import uvicorn
if __name__=="__main__":
    uvicorn.run("src.app:app",host="127.0.0.1",port=int(os.getenv("PORT","8012")),reload=False)
