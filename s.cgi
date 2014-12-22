#!/usr/bin/perl

use strict;
use warnings;

use CGI qw/:standard/;
use Template;
use Mail;
use DBI;
use CGI::Cookie;

require './config.pl';

our $DISK_USAGE;

my $cgi = CGI->new();
my $action = $cgi->param("action");
if ($action eq "logout") {
	my $cookie = cookie( -name => "auth",
		             -value => 0);
	print "Set-Cookie: $cookie\n";
        print $cgi->redirect("/");
        exit 0;
}

my $username = $cgi->cookie("username");
my $password = $cgi->param("password");
my $cookie = $cgi->cookie("auth");

my $status = check_cookie($cookie, $username);
my $directory = $cgi->param("directory");

if ($status) {
        $username = $cgi->cookie("username");
        my $dbh = dbh_connect();
        my $SQL = "SELECT password FROM users WHERE username = ?";
        my $sth = $dbh->prepare($SQL);
        $sth->execute($username);
        $password = $sth->fetchrow();
} else {
        $username = $cgi->param("username");
        $password = $cgi->param("password");
        if ($password eq "") {
                $password = $cgi->cookie("password");
        }
if ($username eq "") {
        browser_message("You did not input a valid username." , "");
}
if ($password eq "") {
        $password = $cgi->param("password");
}
if ($password eq "") {
        browser_message("You did not input a valid password.", "");
}
}

if ($password eq "") {
	$password = $cgi->param("password");
}

my $template_path = "templates/show";

print "Content-type: text/html\r\n\r\n";


my $dbh = dbh_connect();

my $SQL = "SELECT * FROM files WHERE public = ?";
my $sth = $dbh->prepare($SQL);
$sth->execute('0');
my @records = ();
my $i = 0;
while (my $record = $sth->fetchrow_hashref()) {
	$records[$i++] = $record;
}
my $template = Template->new();

my $vars = {
	PICTURES => \@records,
};

$template->process($template_path, $vars);
	
exit 0;


