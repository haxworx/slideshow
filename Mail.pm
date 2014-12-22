use strict;
use warnings;

use IO::Socket;

=head1 NAME

Mail Simple POP3 and SMTP module

=head1 DESCRIPTION

This is a module which makes the retrieval of POP3 mail
messages simpler, allows sending of SMTP via Unix sendmail
and includes raw SMTP interaction.
  
It returns a hash with all the message data in POP3 mode,
and simply sends the mail in SMTP mode either via raw 
sockets or using Unix sendmail.

=head1 SYNOPSIS POP3

use Mail;

my $POP3 = Mail->POP3_Connect( host => "shell.fwis.org",
			       user => "warren",
			       pass => "carsales" );
	
my $mail = $POP3->Recv;	

=head1 SYNOPSIS SMTP

use Mail;

my $smtp = Mail->SMTP_Connect( host => "poole.fm",
			       port => 25 );
			       
$smtp->Send( to      => 'alastairpoole@gmail.com',
	     from    => 'warren@247ads.com.au',
	     subject => 'This is a subject',
	     body    => 'This is a message!');

=cut

package Mail;

our $CRLF     = "\r\n";
our $POP3_OK  = qr{\A\+OK};
our $POP3_EOF = qr{\A\.\r\n\z};

our $SLASH    = '/';

sub error {
	my ($this, $message) = @_;
	die "Error: $message\n";
	exit(1);
}

sub send {
	my ($this, $data) = @_;
	my $sock = $this->socket;
	print $sock $data . $CRLF;
}

sub receive {
	my ($this) = @_;
	my $sock = $this->socket;
	$this->{'data'} = <$sock>;
}

sub socket {
	my ($this) = @_;
	return $this->{'sock'};
}

sub pass {
	my ($this) = @_;
	return $this->{'pass'};
}

sub user {
	my ($this) = @_;
	return $this->{'user'};
}



sub Login {
	my ($this, $type) = @_;

	$this->{'type'} = $type;

	if ($type eq 'POP3') {
		
		if ($this->receive !~ m{$POP3_OK}) {
			error "Unknown protocol";
		}
		if ($this->pop3_command("USER" . " " . $this->user)) {
			if ($this->pop3_command("PASS" . " " . $this->pass)) {
				return 0;
			} else {
				$this->error("Authentication failure");
			}
		} else {
			$this->error("Command USER failed");
		}
	} elsif ($type eq 'SMTP') {
		#FIXME: to be implemented...
	} else {
		$this->error("Unimplemented Login type");
	}
}

sub SMTP_Connect {
	my ($class, %args) = @_;
	
	my $this = {
		host => $args{'host'},
		port => $args{'port'} || 25,
		user => $args{'user'} || undef,
		pass => $args{'pass'} || undef,
		data => undef,
		type => $args{'type'} || undef,
		mesg => {
			to      => undef,
			from    => undef,
			subject => undef,
			body    => undef
		},
		sock => undef		
	};
	
	bless $this, $class;

	if (! defined $this->{'type'} || $this->{'type'} ne 'sendmail') {  # XXX logic corrected

		$this->{sock} = IO::Socket::INET->new(
				PeerAddr => $this->{'host'},
				PeerPort => $this->{'port'},
				Blocking => 1,
				Proto    => 'tcp'
		) or $this->error("Cannot connect to $this->{'host'} on port $this->{'port'} - $!");
	
		if (defined $this->{'user'} || defined $this->{'pass'}) {
			if ($this->Login('SMTP') != 0) {
		
			}
		}
	}



	return $this;
}

sub smtp_command {
	my ($this, $cmd) = @_;
	
	my $SMTP_OK = qr{\A250.+};

	$this->send($cmd);
	$this->receive;

	if ($this->{'data'} =~ m{$SMTP_OK}) {
		return 1;
	}

	return 0;
}

sub sendmail {
	my ($this) = @_;
	
	my $sendmail_path = "/usr/sbin/sendmail";
	
	open(SMTP, "|$sendmail_path -oi -t")
		or $this->error("Unable to open $sendmail_path - $!");

	
	print SMTP "From: $this->{'mesg'}->{'from'}\n";
	print SMTP "To: $this->{'mesg'}->{'to'}\n";
	print SMTP "Subject: $this->{'mesg'}->{'subject'}\n";
	if ($this->{'mesg'}->{'content-type'}) {
		print SMTP "MIME-Version: 1.0\n";
		print SMTP "Content-type: $this->{'mesg'}->{'content-type'}\n";
	}
	print SMTP "\n";  # XXX sam added this
	print SMTP "$this->{'mesg'}->{'body'}\n";
	
	close(SMTP);
}

sub smtp_raw {
	my ($this) = @_;

	$this->receive;
	my $host = 'localhost';
	$this->smtp_command("HELO $host");
	$this->send("MAIL FROM: $this->{'mesg'}->{'from'}");
	$this->send("RCPT TO: $this->{'mesg'}->{'to'}");
	$this->send("Subject: $this->{'mesg'}->{'subject'}");
	$this->send("$this->{'mesg'}->{'body'}");
	$this->smtp_command("$CRLF\.$CRLF");
	$this->receive;
	print $this->{'data'} . "\n";
	close $this->socket;
}

sub Sendmail {
	my ($class, %args) = @_;

	my $this = $class->SMTP_Connect(type => 'sendmail');

	return $this;
}

sub Send {
	my ($this, %args) = @_;
	
	if (! defined $args{'to'} || ! defined $args{'from'}
		|| ! defined $args{'subject'} || ! defined $args{'body'}) {
		$this->error("SMTP_Send - missing argument");
	}
	
	foreach my $k (keys(%args)) {
		$this->{'mesg'}->{$k} = $args{$k};
	}
	
	if (exists $this->{'type'} && $this->{'type'} eq 'sendmail') {
		$this->sendmail;
	} else {
		$this->smtp_raw;
	}
}

sub POP3_Connect {
	my ($class, %args) = @_;
	
	my $this = {
		host => $args{'host'},
		port => $args{'port'} || 110,
		user => $args{'user'},
		pass => $args{'pass'},
		data => undef,
		sock => undef
	};
	
	bless $this, $class;
	
	$this->{sock} = IO::Socket::INET->new(
			PeerAddr => $this->{'host'},
			PeerPort => $this->{'port'},
			Blocking => 1,
			Proto    => 'tcp'
	) or $this->error("Cannot connect to $this->{'host'} on port $this->{'port'} - $!");

	if ($this->Login('POP3') != 0) {
	
	}
	
	return $this;
}

sub pop3_command {
	my ($this, $cmd) = @_;

	$this->send($cmd);

	$this->receive;
	if ($this->{'data'} =~ m{$POP3_OK}) {
		return 1;
	}

	return 0;
}

sub pop3_message_count {
	my ($this) = @_;
	my $count = 0;
	
	$this->send("LIST");
	
	my $received = "";
	while ($received !~ m{$POP3_EOF}) {
		$received = $this->receive;
		if ($received =~ m{$POP3_OK\s+(\d+)\s+messages}) {
			$count = $1;
		}
	}
	
	return $count;
}

sub Recv {
	my ($this) = @_;
	
	my $msgs = $this->pop3_message_count;
	return undef if ($msgs == 0);
	
	my %fields = (
		to      => '\ATo:\s+(.+)\r\n\z',
		from    => '\AFrom:\s+(.+)\r\n\z',
		subject => '\ASubject:\s+(.+)\r\n\z',
		date    => '\ADate:\s+(.+)\r\n\z',
		origin  => '\A(Received:.+)\r\n\z',
		junk    => '\A(.+)-(.+):.+\r\n\z'
	);

	my %data_hash  = ();
	my $text       = "";
	my $encoding   = "text/plain";
	my $attachment = 0;
	my $filename   = "";
	my $file_data  = ();
	
	for (my $i = 1; $i <= $msgs; $i++) {
		$this->send("RETR $i");	
		my $received = "";

		while ($received !~ m{$POP3_EOF}) {
			$received = $this->receive;
	
			$text .= $received;
			
			if ($received =~ m{\AContent-Transfer-Encoding:\s+(.+)\z}) {
				$encoding = $1;
			}
				
			if ($received =~ m{\s+filename="(.+)"\z}) {
				$filename = $1;
				$data_hash{$i}->{'attachments'}->{$filename} = { filename => $filename,
										 data     => undef };
				$attachment = 1;
				$received = "";
				next;
			}	
				
			if ($received =~ m{-+.+NextPart.+\z} && $attachment) {
				if ($encoding eq 'base64') {
					$file_data = MIME::Base64::decode($file_data);
				}

				$data_hash{$i}->{'attachments'}->{$filename}->{'data'} = $file_data;
				$attachment = 0;
				$file_data = ();
			}
				
			if ($attachment) {
				$file_data .= $received;
			} else {			
				foreach my $field (keys(%fields)) {
					my $regex = $fields{$field};
					if ($received =~ m{$regex}) {
						$data_hash{$i}->{$field} = $1;
					} 
				}
			}
			
		}
			
		$data_hash{$i}->{text} = $text;
		$this->send("DELE $i"); # Delete the message
		$this->receive;         # For +OK response...
	}
	
	return \%data_hash;
}

1;
