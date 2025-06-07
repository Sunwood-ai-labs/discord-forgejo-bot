import aiohttp

class ForgejoAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
    
    async def create_issue(self, owner, repo, title, body, assignee=None, labels=None):
        """Forgejoにissueを作成"""
        url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues"
        
        data = {
            'title': title,
            'body': body
        }
        
        if assignee:
            data['assignee'] = assignee
        if labels:
            data['labels'] = labels
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Failed to create issue: {response.status} - {text}")
    
    async def get_issue(self, owner, repo, issue_number):
        """指定したissueの詳細を取得"""
        url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues/{issue_number}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

    async def create_comment(self, owner, repo, issue_number, body):
        """指定したissueにコメントを追加"""
        url = f"{self.base_url}/api/v1/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {
            'body': body
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Failed to create comment: {response.status} - {text}")