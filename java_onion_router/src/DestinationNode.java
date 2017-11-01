import java.io.*;
import java.net.*;

public class DestinationNode
{
	public static void main(String[] args) throws Exception
	{	
		// Port 14444 => Destination Node
		ServerSocket welcomeSocket = new ServerSocket(14444);
		
		while(true)
		{
			// Receive from onion node #3.
			Socket connectionSocket = welcomeSocket.accept();
			BufferedReader inFromOnionNode3 = new BufferedReader(new InputStreamReader(connectionSocket.getInputStream()));
			String receiveMessage = inFromOnionNode3.readLine();
			printReceivedMessage(connectionSocket.getInetAddress(), connectionSocket.getPort(), receiveMessage);
			
			// Convert message to upper case.
			String sendMessage = receiveMessage.toUpperCase();
			
			// Send back to onion node #3.
			DataOutputStream outToOnionNode3 = new DataOutputStream(connectionSocket.getOutputStream());
			outToOnionNode3.writeBytes(sendMessage + '\n');
		}
	}
	
	public static void printReceivedMessage(InetAddress address, int port, String message)
	{
		System.out.println("");
		System.out.println("Destination Node received a message");
		System.out.println("===================================");
		System.out.println("Source IP Address:  " + address);
		System.out.println("Source Port Number: " + port);
		System.out.println("Content:            " + message);
	}
}
