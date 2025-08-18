# Serve generic profile template and pass UIID to frontend
import os
import base64
import requests
import json
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string

# Correct import for google-generativeai
import google.generativeai as genai
from google.generativeai import types

app = Flask(__name__)

# Serve generic profile template and pass UIID to frontend
profile_template_html = r'''
<!DOCTYPE html>
<html lang="en">
<head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TagMe.AI Profile</title>
        <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #fafbfc; margin: 0; }
                .container { max-width: 700px; margin: 40px auto; background: white; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.07); padding: 40px; }
                .uiid { font-size: 1em; color: #667eea; margin-bottom: 20px; font-family: monospace; }
                h1 { font-size: 2.2em; margin-bottom: 10px; }
                h3 { color: #666; margin-bottom: 30px; }
                .blog-body { margin-top: 30px; color: #333; line-height: 1.6; }
                .error { background: #ffebee; color: #c62828; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #c62828; }
        </style>
</head>
<body>
        <div class="container" id="profileContainer">
                <div class="uiid" id="uiidDisplay"></div>
                <h1 id="blogTitle"></h1>
                <h3 id="blogSubtitle"></h3>
                <div class="blog-body" id="blogBody"></div>
        </div>
        <script type="module">
            import { initializeApp } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js";
            import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-database.js";

            const firebaseConfig = {
                apiKey: "AIzaSyBo-iuUmIVgcBYWG8ltWgugkVbfqFUf4wg",
                authDomain: "fronti-login.firebaseapp.com",
                databaseURL: "https://fronti-login-default-rtdb.asia-southeast1.firebasedatabase.app",
                projectId: "fronti-login",
                storageBucket: "fronti-login.firebasestorage.app",
                messagingSenderId: "403453632821",
                appId: "1:403453632821:web:7583bc00458748e447ac7c",
                measurementId: "G-GH16N4RN8S"
            };
            const app = initializeApp(firebaseConfig);
            const db = getDatabase(app);

            // Get UIID from backend (injected into JS)
            const uiid = "{{ uiid }}";

            async function loadProfile() {
                if (!uiid) {
                    document.getElementById('profileContainer').innerHTML = '<div class="error">No UIID found in URL.</div>';
                    return;
                }
                // Firebase does not allow . # $ [ ] in keys
                const safeUiid = uiid.replace(/[.#$\[\]]/g, '_');
                try {
                    const snapshot = await get(ref(db, 'profiles/' + safeUiid));
                    if (!snapshot.exists()) {
                        document.getElementById('profileContainer').innerHTML = `<div class="error">No profile found for UIID: ${uiid}</div>`;
                        return;
                    }
                    const data = snapshot.val();
                    document.getElementById('uiidDisplay').textContent = 'UIID: ' + (data.output?.uiid || uiid);
                    document.getElementById('blogTitle').textContent = data.output?.blog?.title || 'No Title';
                    document.getElementById('blogSubtitle').textContent = data.output?.blog?.subtitle || '';
                    document.getElementById('blogBody').innerHTML = (data.output?.blog?.body || '').replace(/\n/g, '<br>');
                } catch (error) {
                    document.getElementById('profileContainer').innerHTML = `<div class="error">Error loading profile: ${error.message}</div>`;
                }
            }
            loadProfile();
        </script>
</body>
</html>
'''

@app.route('/profile/<uiid>')
def serve_profile(uiid):
        # Pass UIID to frontend template
        return render_template_string(profile_template_html, uiid=uiid)
import os
import base64
import requests
import json
from flask import Flask, request, jsonify, send_file, send_from_directory
from google import genai
from google.genai import types

API_KEY = "AIzaSyB8WRNReeJkKJfUkmU2WuyztBYFEmNl2Vg"
DEV_API_KEY = "n51PDg1CMRSWGYFnnWXBfvKV"

app = Flask(__name__)

# Store blogs by uiid
blogs_by_uiid = {}

# Serve the TagMe.AI UI from the backend
@app.route('/')
def serve_tagme_ui():
    html_path = os.path.join(os.path.dirname(__file__), 'tagme_ui.html')
    if not os.path.exists(html_path):
        return "tagme_ui.html not found", 404
    return send_file(html_path)

@app.route('/create-profile', methods=['POST'])
def create_profile():
    """Create a new TagMe.AI profile"""
    data = request.json
    # Get UIID from form data
    uiid = data.get('uiid', '').lower().strip()
    if not uiid:
        name = data.get('name', '')
        uiid = generate_uiid_from_name(name)
    import uuid
    profile_uuid = str(uuid.uuid4())
    blog_content = generate_ai_blog(data)
    blogs_by_uiid[uiid] = blog_content
    return jsonify({
        'success': True,
        'uuid': profile_uuid,
        'uiid': uiid,
        'profile_url': f'/profile/{uiid}',
        'blog_url': f'/blog/{uiid}'
    })

# Route to show the blog for a specific uiid
@app.route('/blog/<uiid>')
def show_blog(uiid):
    blog = blogs_by_uiid.get(uiid)
    if not blog:
        return f"No blog found for UIID: {uiid}", 404
    title = blog.get('title', '')
    subtitle = blog.get('subtitle', '')
    body = blog.get('body', '')
    # SEO meta tags
    meta_title = title if title else f"{uiid} - TagMe.AI Blog"
    meta_description = subtitle if subtitle else (body[:160].replace('\n', ' ') if body else f"Discover {uiid} on TagMe.AI")
    canonical_url = f"https://fronti.tech/tagmeai/blog/{uiid}"
    og_title = meta_title
    og_description = meta_description
    og_url = canonical_url
    # Render HTML with SEO tags
    html = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>{meta_title}</title>
        <meta name='description' content='{meta_description}'>
        <link rel='canonical' href='{canonical_url}'>
        <!-- Open Graph -->
        <meta property='og:title' content='{og_title}'>
        <meta property='og:description' content='{og_description}'>
        <meta property='og:url' content='{og_url}'>
        <meta property='og:type' content='article'>
        <!-- Twitter Card -->
        <meta name='twitter:card' content='summary_large_image'>
        <meta name='twitter:title' content='{og_title}'>
        <meta name='twitter:description' content='{og_description}'>
        <style>
            body {{ font-family:sans-serif; max-width:700px; margin:40px auto; background:#fafbfc; }}
            .blog-container {{ background:white; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.07); padding:40px; }}
            h1 {{ font-size:2.2em; margin-bottom:10px; }}
            h3 {{ color:#666; margin-bottom:30px; }}
            .uiid {{ font-size:1em; color:#667eea; margin-bottom:20px; font-family:monospace; }}
        </style>
    </head>
    <body>
        <div class='blog-container'>
            <div class='uiid'>UIID: {uiid}</div>
            <h1>{title}</h1>
            <h3>{subtitle}</h3>
            <div style='margin-top:30px;'>{body.replace('\n', '<br>')}</div>
            <a href='/' style='display:block;margin-top:40px;color:#667eea;'>Back to Profile Form</a>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/generate-blog', methods=['POST'])
def generate_blog():
    data = request.json
    name = data.get('name', '')
    about = data.get('about', '')
    info = data.get('info', '')
    x = data.get('x', '')
    instagram = data.get('instagram', '')
    other = data.get('other', '')

    prompt = f"""
    You are an expert blog writer. Write a professional blog post based on the following user information.
    Please return your response as a JSON object with the following fields:
    {{
      "title": "...",
      "subtitle": "...",
      "body": "..."
    }}
    Name: {name}
    About: {about}
    Info for AI: {info}
    X (Twitter): {x}
    Instagram: {instagram}
    Other Social Media: {other}
    """

    client = genai.Client(api_key=API_KEY)
    model = "gemini-2.5-pro"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    # No external tools needed here
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )
    try:
        blog_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            blog_text += chunk.text
        # Try to parse the JSON from Gemini's response
        import json
        def extract_blog_parts(text):
            import re
            title, subtitle, body = '', '', ''
            # Try to extract using labeled sections
            title_match = re.search(r'\*\*Title:\*\*\s*(.*?)(\*\*|\n|$)', text)
            subtitle_match = re.search(r'\*\*Subtitle:\*\*\s*(.*?)(\*\*|\n|$)', text)
            body_match = re.search(r'\*\*Body:\*\*\s*(.*)', text, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
            if subtitle_match:
                subtitle = subtitle_match.group(1).strip()
            if body_match:
                body = body_match.group(1).strip()
            # Fallback: try to find lines starting with Title/Subtitle/Body
            if not title:
                line_title = re.search(r'^Title:\s*(.*)', text, re.MULTILINE)
                if line_title:
                    title = line_title.group(1).strip()
            if not subtitle:
                line_subtitle = re.search(r'^Subtitle:\s*(.*)', text, re.MULTILINE)
                if line_subtitle:
                    subtitle = line_subtitle.group(1).strip()
            if not body:
                line_body = re.search(r'^Body:\s*(.*)', text, re.MULTILINE | re.DOTALL)
                if line_body:
                    body = line_body.group(1).strip()
            # If still not found, treat all as body
            if not title and not subtitle:
                body = text.strip()
            return {'title': title or 'No title', 'subtitle': subtitle, 'body': body}

        try:
            blog_json = json.loads(blog_text)
        except Exception:
            blog_json = extract_blog_parts(blog_text)
        # Refine and normalize
        blog_json = refine_blog(blog_json, fallback_author=name)

        # Send to dev.to
        DEV_API_KEY = os.getenv('DEV_API_KEY', 'n51PDg1CMRSWGYFnnWXBfvKV')
        headers = {
            "api-key": DEV_API_KEY,
            "Content-Type": "application/json"
        }
        # Compose markdown body (add subtitle if present)
        body_markdown = f"\n### {blog_json.get('title', '')}\n\n"
        if blog_json.get('subtitle'):
            body_markdown += f"**{blog_json['subtitle']}**\n\n"
        body_markdown += blog_json.get('body', '')
        article_data = {
            "article": {
                "title": blog_json.get('title', ''),
                "published": True,
                "body_markdown": body_markdown,
                "tags": ['ai', 'blog'],
                "series": '',
                "canonical_url": ''
            }
        }
        dev_response = requests.post("https://dev.to/api/articles", headers=headers, json=article_data)
        if dev_response.status_code == 201:
            dev_result = {"success": True, "url": dev_response.json().get("url")}
        else:
            dev_result = {"success": False, "error": dev_response.text}

        return jsonify({"blog": blog_json, "dev": dev_result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

##def publish_to_dev_to(blog_content, author_name):#
    #"""Publish blog content to DEV.to"""
    #try:
        #DEV_API_KEY = os.getenv('DEV_API_KEY', 'n51PDg1CMRSWGYFnnWXBfvKV')
        #headers = {
            #"api-key": DEV_API_KEY,
            #"Content-Type": "application/json"
        #}
        
        # Compose markdown body for DEV.to
        #body_markdown = f"# {blog_content.get('title', '')}\n\n"
        #if blog_content.get('subtitle'):
            #body_markdown += f"*{blog_content['subtitle']}*\n\n"
        
        # Convert body to proper markdown format
        #body_text = blog_content.get('body', '')
        # Ensure proper paragraph breaks for markdown
        #body_text = body_text.replace('\n\n', '\n\n')
        #body_markdown += body_text
        
        # Add TagMe.AI signature
        #body_markdown += f"\n\n---\n\n*This profile was created using [TagMe.AI](https://tagme.ai) - Your AI-Readable Digital Identity*"
        
        # Get UIID from blog content for canonical URL
        #uiid = blog_content.get('uiid', '')
        #       canonical_url = f"https://fronti.tech/tagmeai/{uiid}" if uiid else ""
        
        # Sanitize title for safety (remove code fences/backticks)
        #safe_title = (blog_content.get('title', f'Meet {author_name} - TagMe.AI Profile') or '').replace('```', '').replace('`', '').strip()
        #article_data = {
            #"article": {
                #"title": safe_title,
                #"published": True,
                #"body_markdown": body_markdown,
                # DEV.to tags must be alphanumeric
                #"tags": ['ai', 'digitalidentity', 'tagmeai', 'profile'],
                #"series": 'TagMe AI Profiles',
                #"canonical_url": canonical_url
            #}
        #}
        
        #print(f"Publishing to DEV.to with API key: {DEV_API_KEY[:10]}...")
        #print(f"Article title: {article_data['article']['title']}")
     
def extract_blog_parts(text):
    """Parse model text output into a dict with title, subtitle, body."""
    import re
    title, subtitle, body = '', '', ''
    # Bold-labeled sections
    title_match = re.search(r'\*\*Title:\*\*\s*(.*?)(\*\*|\n|$)', text)
    subtitle_match = re.search(r'\*\*Subtitle:\*\*\s*(.*?)(\*\*|\n|$)', text)
    body_match = re.search(r'\*\*Body:\*\*\s*(.*)', text, re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
    if subtitle_match:
        subtitle = subtitle_match.group(1).strip()
    if body_match:
        body = body_match.group(1).strip()
    # Fallback plain labels
    if not title:
        line_title = re.search(r'^Title:\s*(.*)', text, re.MULTILINE)
        if line_title:
            title = line_title.group(1).strip()
    if not subtitle:
        line_subtitle = re.search(r'^Subtitle:\s*(.*)', text, re.MULTILINE)
        if line_subtitle:
            subtitle = line_subtitle.group(1).strip()
    if not body:
        line_body = re.search(r'^Body:\s*(.*)', text, re.MULTILINE | re.DOTALL)
        if line_body:
            body = line_body.group(1).strip()
    if not title and not subtitle and not body:
        body = text.strip()
    return {'title': title or 'No title', 'subtitle': subtitle, 'body': body}

def _generate_title_from_text(text: str, fallback: str = "") -> str:
    cleaned = (text or "").strip().replace("\n", " ")
    if not cleaned:
        return fallback or "Untitled"
    snippet = " ".join(cleaned.split()[:12])
    # Simple sentence-case to title-like form
    return snippet[:1].upper() + snippet[1:]

def refine_blog(blog_json: dict, fallback_author: str = "") -> dict:
    """Normalize and refine model output into a single coherent blog dict.

    Ensures a non-empty title/subtitle and flattens sections/paragraphs into one body.
    """
    if not isinstance(blog_json, dict):
        blog_json = {}

    title = (blog_json.get('title') or '').strip()
    subtitle = (blog_json.get('subtitle') or '').strip()
    body = blog_json.get('body')
    sections = blog_json.get('sections') or blog_json.get('paragraphs') or []

    # Flatten sections/paragraphs if provided
    combined_parts: list[str] = []
    if isinstance(sections, list) and sections:
        for section in sections:
            if isinstance(section, dict):
                sec_title = (section.get('title') or section.get('heading') or '').strip()
                sec_content = (section.get('body') or section.get('content') or section.get('text') or '').strip()
                if sec_title:
                    combined_parts.append(f"## {sec_title}\n\n{sec_content}" if sec_content else f"## {sec_title}")
                elif sec_content:
                    combined_parts.append(sec_content)
            elif isinstance(section, str) and section.strip():
                combined_parts.append(section.strip())

    if not body and combined_parts:
        body = "\n\n".join(combined_parts)

    if not isinstance(body, str):
        body = body if body is not None else ""
        body = str(body)
    body = body.strip()

    # Ensure title
    if not title or title.lower() == 'no title':
        candidate_source = subtitle or body
        fallback = f"Meet {fallback_author}".strip() if fallback_author else ""
        title = _generate_title_from_text(candidate_source, fallback)

    # Ensure subtitle
    if not subtitle:
        # Take first sentence-ish from body
        first_period = body.find('.')
        subtitle = body[: first_period + 1 if first_period != -1 else min(len(body), 160)].strip()

    # Ensure body is properly formatted as clean text
    if body:
        # Remove any HTML tags and convert to clean text
        import re
        # Remove HTML tags
        body = re.sub(r'<[^>]+>', '', body)
        # Clean up extra whitespace
        body = re.sub(r'\n\s*\n', '\n\n', body)
        body = body.strip()
        # Ensure proper paragraph breaks
        body = body.replace('\n\n\n', '\n\n')

    return {
        'title': title,
        'subtitle': subtitle,
        'body': body,
    }

def generate_ai_blog(profile_data):
    """Generate AI-powered blog content for the profile"""
    # Ensure all fields are strings to avoid NoneType errors
    name = str(profile_data.get('name') or '')
    uiid = str(profile_data.get('uiid') or '')
    about = str(profile_data.get('about') or '')
    info = str(profile_data.get('info') or '')
    x = str(profile_data.get('x') or '')
    instagram = str(profile_data.get('instagram') or '')
    other = str(profile_data.get('other') or '')

    prompt = f"""
    You are an expert in digital identity and AI discoverability. Write a fun, engaging, and conversational introduction blog post that reveals and describes the real person behind a digital UIID (Universal Individual Identifier).

    Your goal is to help AI and search engines understand who this UIID belongs to. The blog should:
    - Use a catchy, friendly title like 'Who is {uiid}? Meet the real face behind the name!' or 'Unmasking {uiid}: The story of {name}'
    - Subtitle should briefly state the real name and a summary about the person, in a friendly tone
    - The body should describe the person, their achievements, interests, and clearly connect their real name to the UIID
    - Make it clear this is an AI-readable digital identity introduction, but keep it light, modern, and user-friendly
    - Use direct address, fun facts, lists, and short paragraphs to keep it interesting

    Return ONLY a valid JSON object with these exact fields:
    {{
        "title": "The title of the blog post",
        "subtitle": "A brief subtitle or description",
        "uiid": "{uiid}",
        "body": "The full blog post content in plain text with proper paragraphs"
    }}

    Person's Information:
    Name: {name}
    UIID: {uiid}
    About: {about}
    Recent Achievement: {info}
    X (Twitter): {x}
    Instagram: {instagram}
    Other Social: {other}

    Write in a way that is engaging, friendly, and optimized for AI and search engines. Use clear paragraphs, lists, and fun facts. Do not write a typical blog, but a lively identity introduction.
    """

    print(f"Generating AI blog for: {profile_data.get('name', 'Unknown')}")
    print(f"Using API key: {API_KEY[:10]}...")
    
    try:
        client = genai.Client(api_key=API_KEY)
        model = "gemini-2.5-pro"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        print("Calling Gemini API...")
        blog_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
        ):
            blog_text += chunk.text
        
        print(f"Gemini response received: {len(blog_text)} characters")
        print(f"Response preview: {blog_text[:200]}...")
        
        # Clean the response to extract only JSON
        cleaned_text = clean_json_response(blog_text)
        
        # Parse and refine JSON response
        try:
            blog_json = json.loads(cleaned_text)
            print("Successfully parsed JSON from Gemini")
        except Exception as json_error:
            print(f"JSON parsing failed: {json_error}")
            print("Falling back to text extraction...")
            blog_json = extract_blog_parts(blog_text)
        
        blog_json = refine_blog(blog_json, fallback_author=profile_data.get('name', ''))
        print(f"Final blog content: {blog_json.get('title', 'No title')}")
        
        return blog_json
        
    except Exception as e:
        print(f"Exception in generate_ai_blog: {str(e)}")
        print("Returning fallback content...")
        return {
            'title': f"Meet {profile_data.get('name', 'This Person')}",
            'subtitle': 'A TagMe.AI Digital Identity',
            'body': f"<p>Welcome to the AI-readable profile of {profile_data.get('name', 'this person')}. This profile is structured for AI systems and search engines to discover and understand.</p>"
        }

@app.route('/profile/<uiid>')
def view_profile(uiid):
    """View a TagMe.AI profile"""
    # For now, return a simple profile page
    # In a full implementation, you'd fetch from database
    profile_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TagMe.AI Profile - {uiid}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; min-height: 100vh; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }}
            .profile-section {{ padding: 40px 20px; }}
            .uuid-display {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; border: 2px dashed #667eea; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TagMe.AI Profile</h1>
                <p>AI-Readable Digital Identity</p>
            </div>
            <div class="profile-section">
                <div class="uuid-display">
                    <strong>TagMe UIID:</strong><br>
                    {uiid}
                </div>
                <h2>Profile Information</h2>
                <p>This is a TagMe.AI profile with AI-readable structured data.</p>
                <p>Profile data would be loaded from the database in a full implementation.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return profile_html

@app.route('/api/profiles')
def list_profiles():
    """List all TagMe profiles (for AI directory)"""
    # For now, return empty list
    # In a full implementation, you'd fetch from database
    return jsonify([])



def generate_uiid_from_name(name):
    """Generate UIID from name"""
    import re
    if not name:
        return "user"
    
    # Convert to lowercase and remove special characters
    uiid = re.sub(r'[^a-z0-9\s]', '', name.lower())
    # Replace spaces with dots
    uiid = re.sub(r'\s+', '.', uiid)
    # Remove multiple dots
    uiid = re.sub(r'\.+', '.', uiid)
    # Remove leading/trailing dots
    uiid = uiid.strip('.')
    
    return uiid if uiid else "user"

def clean_json_response(text):
    """Clean the response to extract only valid JSON"""
    import re
    
    # Try to find JSON object in the text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        # Find the longest match (most likely to be the complete JSON)
        longest_match = max(matches, key=len)
        print(f"Found JSON match: {longest_match[:100]}...")
        return longest_match
    
    # If no JSON found, try to extract content between curly braces
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        json_text = text[start:end+1]
        print(f"Extracted JSON from braces: {json_text[:100]}...")
        return json_text
    
    print("No JSON found in response, returning original text")
    return text

def test_gemini_api():
    """Test if Gemini API is working"""
    try:
        print("Testing Gemini API...")
        client = genai.Client(api_key=API_KEY)
        model = "gemini-2.5-pro"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Say 'Hello, Gemini is working!'")],
            ),
        ]
        
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
        
        print(f"Gemini API test successful: {response.text}")
        return True
    except Exception as e:
        print(f"Gemini API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test Gemini API before starting
    if not test_gemini_api():
        print("WARNING: Gemini API is not working. Blog generation will use fallback content.")
    
    app.run(debug=True)



