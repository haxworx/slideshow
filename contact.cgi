#!/usr/bin/perl

use strict;
use warnings;

use CGI qw/:standard/;
use Template;
use Mail;
use DBI;
use Crypt::PasswdMD5 qw(unix_md5_crypt);

require './config.pl';

my $cgi = CGI->new();

my $name = $cgi->param("name");
my $email = $cgi->param("email");
my $text = $cgi->param("description");

$name =~ s{(['%])}{\\$1}g;
$email =~ s{(['%])}{\\$1}g;
$text =~ s{(['%])}{\\$1}g;

if ($name eq "" || $email eq "" || $text eq "") {
	browser_message("Missing fields, try again!");
}

if (uc($email) !~ /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/) {
	browser_message("Invalid e-mail address, try again!");
}

my $data = {
	"NAME"    => $name,
	"EMAIL"   => $email,
	"TEXT" => $text,
};

my $template = Template->new();
my $body = "";
$template->process("templates/enquiry", $data, \$body);

my $sendmail = Mail->Sendmail();

$sendmail->Send('to' => 'alastair@showenergy.net',
		'from' => $email,
		'subject' => 'Haxlab.net Enquiry',
		'body' => $body);

browser_message("Your enquiry has been sent and should be responded to within 48 hours. Thank you for your interest!");
exit 0;
