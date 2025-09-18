/**
 * Server-Sent Events service for real-time AI operation updates.
 */
export class SSEService {
    private eventSource: EventSource | null = null;
    private pollInterval: NodeJS.Timeout | null = null;
    
    /**
     * Connect to AI operation status endpoint.
     * @param operationId - The AI operation ID to track
     * @param onMessage - Callback for received messages
     * @param onError - Optional error callback
     */
    connect(
        operationId: string, 
        onMessage: (data: any) => void, 
        onError?: (error: Event) => void
    ): void {
        // Use polling instead of SSE for now
        // TODO: Implement proper SSE when StreamingHttpResponse is fixed
        const url = `http://localhost:8000/api/ai-operations/${operationId}/stream/`;
        
        // Poll the endpoint every 1 second until completed or failed
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(url, {
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                console.log('SSE Service received data:', data);
                
                // Transform the response to match the expected SSE format
                const transformedData = {
                    status: data.status === 'COMPLETED' ? 'completed' : 
                           data.status === 'FAILED' ? 'failed' : 
                           data.status === 'PENDING' ? 'pending' :
                           data.status === 'PROCESSING' ? 'processing' : data.status,
                    result: data.status === 'COMPLETED' ? { summary: data.result } : data.result,
                    error: data.error
                };
                console.log('SSE Service transformed data:', transformedData);
                onMessage(transformedData);

                // Stop polling if operation is completed or failed
                if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                    clearInterval(pollInterval);
                }
            } catch (error) {
                console.error('Failed to fetch operation status:', error);
                clearInterval(pollInterval);
                onError?.(error as Event);
            }
        }, 1000); // Poll every 1 second

        // Store the interval ID so we can clear it later
        this.pollInterval = pollInterval;
    }
    
    /**
     * Disconnect from the SSE stream.
     */
    disconnect(): void {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    /**
     * Check if currently connected.
     */
    isConnected(): boolean {
        return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
    }
}

export const sseService = new SSEService();
