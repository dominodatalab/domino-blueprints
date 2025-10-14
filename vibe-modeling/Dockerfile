FROM quay.io/domino/domino-standard-environment:release-6.1.1.latest

USER root

RUN `##### VSCODE #####` && \
    chmod 755 /opt/domino/workspaces/vscode/start && \
    curl -fOL https://github.com/coder/code-server/releases/download/v4.103.0/code-server_4.103.0_amd64.deb && \
    dpkg -i code-server_4.103.0_amd64.deb && \
    rm -rf code-server_4.103.0_amd64.deb

RUN curl -o /tmp/github.copilot.vsix -LSsf https://github.gallery.vsassets.io/_apis/public/gallery/publisher/github/extension/copilot/1.350.0/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage && \ 
    code-server --install-extension /tmp/github.copilot.vsix --force --extensions-dir /home/ubuntu/.local/share/code-server/extensions && rm /tmp/github.copilot.vsix 
RUN curl -o /tmp/github-chat.vsix -LSsf https://github.gallery.vsassets.io/_apis/public/gallery/publisher/github/extension/copilot-chat/0.30.1/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage && \
	code-server --install-extension /tmp/github-chat.vsix --force --extensions-dir /home/ubuntu/.local/share/code-server/extensions && rm /tmp/github-chat.vsix 

# Add MCP configuration to existing start script
COPY <<EOF /tmp/modify_start.py
import re

# Read the current start script
with open('/opt/domino/workspaces/vscode/start', 'r') as f:
    content = f.read()

# Define the MCP configuration block
mcp_config = '''
# Setup MCP configuration
MCP_FILE="\${SETTINGS_DIR}/User/mcp.json"
mkdir -p "\${SETTINGS_DIR}/User/"
if [ ! -f "\$MCP_FILE" ]; then
    cat << MCPEOF > "\$MCP_FILE"
{
    "inputs": [],
    "servers": {
        "domino-server": {
            "type": "stdio",
            "command": "python",
            "args": ["/opt/domino/domino_mcp_server/domino_mcp_server.py"]
        }
    }
}
MCPEOF
fi

# Create prompts directory and copy instructions
mkdir -p "\${SETTINGS_DIR}/User/prompts"
cp /opt/domino/domino_mcp_server/resources/domino.instructions.md "\${SETTINGS_DIR}/User/prompts/domino.instructions.md"

# Run code-server
'''

# Insert the MCP configuration before the "# Run code-server" line
modified_content = re.sub(
    r'(# Run code-server)',
    mcp_config,
    content
)

# Write the modified content back
with open('/opt/domino/workspaces/vscode/start', 'w') as f:
    f.write(modified_content)
EOF

RUN python3 /tmp/modify_start.py && rm /tmp/modify_start.py

RUN cd /opt/domino && git clone -b vdhawan-in-domino-mcp https://github.com/dominodatalab/domino_mcp_server && pip install mcp FastMCP requests python-dotenv