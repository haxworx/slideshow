#! /usr/bin/perl

use strict;
use warnings;

use Digest::MD5 qw/md5_hex/;
use CGI qw/:standard/;
use CGI::Cookie;
use DBI;

our $DISK_SPACE = 1000 * (1024 * 1024 * 1024);

our $SECRET = "JesusIsLord";
my @salt = ( '.', '/', 0 .. 9, 'A' .. 'Z', 'a' .. 'z' );

sub gensalt {
  my $count = shift;

  my $salt;
  for (1..$count) {
    $salt .= (@salt)[rand @salt];
  }

  return $salt;
}


sub create_cookie {
	my ($username, $password, $directory) = @_;

	my $secret = "$username:$SECRET";

	my $cookie_value = md5_hex($secret);

	my $time = time();

	my $expires = $time + 60 * 60;

	my $cgi = CGI->new();

	my $cookie = $cgi->cookie( -name => 'auth',
				  -value => $cookie_value);
#			  -expires => $expires );
#
	my $next_cookie = $cgi->cookie( -name => 'username',
					-value => $username);

	my $third_cookie = $cgi->cookie( -name => 'directory',
					 -value => $directory);

	print "Set-Cookie: $cookie\n";
	print "Set-Cookie: $next_cookie\n";
	print "Set-Cookie: $third_cookie\n";

	print "Content-type: text/html\r\n\r\n";
}

sub check_cookie {
	my ($cookie, $username) = @_;

	my $secret = "$username:$SECRET";

	$secret = md5_hex($secret);

	if ($cookie eq $secret) {
		return 1;
	} else {
		return 0;
	}
}

sub browser_message {
        my ($message, $username, $directory) = @_;
	use Template;
        my $template_path = "templates/browser-message";

        my $template = Template->new();

        my $vars = {
                MESSAGE => $message,
		USERNAME => $username,
		DIRECTORY => $directory,
        };

        print "Content-type: text/html\r\n\r\n";
        $template->process($template_path, $vars);

        exit 0;
}

sub dbh_connect {
        my $dsn = "DBI:mysql:database=hacktastic:host=localhost";
        my $dbh = DBI->connect($dsn, 'haxworx', 'vitae') || browser_message("DBH ERROR");

        return $dbh;
}


sub calculate_disk_usage {
	my ($path) = @_;
	opendir(DIR, $path);
	my $MB;
	my @dirs = ();
	while (defined(my $file = readdir(DIR))) {
		if ($file eq "." || $file eq "..") { next; }
		my $fullpath = "$path/$file";
		if (-d $fullpath) {
			push @dirs, $fullpath;
		}
		my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($fullpath);
	
		$MB += $size;
	}

	foreach (@dirs) {
		$MB += calculate_disk_usage($_);
	}
	$MB = int($MB / (1024 * 1024));
	closedir DIR;
	return $MB;
}

sub disk_usage_bytes {
        my ($username) = @_;

        my $path = "users/$username";

        opendir(DIR, $path);

        my $bytes = 0;

        while (defined(my $file = readdir(DIR))) {
                if ($file eq "." || $file eq "..") { next; }
                my $fullpath = "$path/$file";
                my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($fullpath);

                $bytes += $size;
        }

        closedir DIR;

        return $bytes;
}

sub read_dirs {
	my ($username) = @_;

	my $path = "users/$username";

	opendir(DIR, $path);
		
	my @dirs = ();

	my $count = 0;
	while (defined(my $file = readdir(DIR))) {
		my $fullpath = "$path/$file";
		if ($file eq "." || $file eq "..") { next; }
		if (-d $fullpath) {
			push @dirs, $file;
			$count++;
		}	
	}

	closedir DIR;

	@dirs = sort @dirs;

	return @dirs;
}

sub files_table {
	my (@files) = @_;
	my $style = "";
	my $i = 0;



	use Image::Resize;
	foreach my $file (@files) {
		my $filename = "$file->{name}";

		my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($filename);
		my $color = $i % 2;
		if ($color == 0) {
			$style = "rowA";
		} else {
			$style = "rowB";
		}

	
		my $unit = "B";
		if ($size >= 1000 * (1024 * 1024)) {
			$unit = "G";
			$size = int($size / (1024 * 1024 * 1024));
		}
		if ($size >= (1024 * 1024)) {
			$unit = "M";
			$size = int($size / (1024 * 1024));	
		} 

		if ($size >= 1024) {
			$size = int($size / 1024);
			$unit = "K"
		}
		
		$file->{size} = "$size$unit";
		$file->{class} = $style;
		$files[$i++] = $file;
	}
	
	return @files;
}
